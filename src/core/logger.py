import logging
import sys
from abc import ABCMeta
from typing import Any
from functools import wraps
import asyncio

class AsyncHandler(logging.Handler):

    COLOR_MAP = {
        logging.DEBUG: '\033[0m',
        logging.INFO: '\033[0m',
        logging.WARNING: '\033[33m',
        logging.ERROR: '\033[31m',
        logging.CRITICAL: '\033[31m',
    }
    COLOR_RESET = '\033[0m'

    def __init__(self, queue_size: int = 1000):
        super().__init__()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=queue_size)
        self._task: asyncio.Task | None = None
        self._closed = False

        self.setFormatter(self._create_formatter())

    # ---------- Formatter ----------

    def _create_formatter(self) -> logging.Formatter:
        fmt = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'

        class ColoredFormatter(logging.Formatter):
            def format(inner_self, record: logging.LogRecord) -> str:
                msg = super(ColoredFormatter, inner_self).format(record)
                color = AsyncHandler.COLOR_MAP.get(record.levelno, AsyncHandler.COLOR_RESET)
                if color != AsyncHandler.COLOR_RESET:
                    return f"{color}{msg}{AsyncHandler.COLOR_RESET}"
                return msg

        return ColoredFormatter(fmt, datefmt=datefmt)

    # ---------- Public API ----------

    def emit(self, record: logging.LogRecord) -> None:
        if self._closed:
            return

        try:
            msg = self.format(record)
            loop = self._get_loop()

            if loop is not None and loop.is_running():
                if self._task is None:
                    self._task = loop.create_task(self._worker())
                self._enqueue(msg)
            else:
                self._write_sync(msg)

        except Exception:
            self.handleError(record)

    def close(self) -> None:
        self._closed = True
        if self._task:
            self._task.cancel()
        super().close()

    # ---------- Internal ----------

    def _get_loop(self) -> asyncio.AbstractEventLoop | None:
        """Return running loop or None if not available."""
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = None
        return self.loop

    def _enqueue(self, msg: str) -> None:
        try:
            self.queue.put_nowait(msg)
        except asyncio.QueueFull:
            sys.stderr.write("[LOGGING] Queue overflow, log dropped\n")

    async def _worker(self) -> None:
        """Background task to process log messages from queue."""
        try:
            while True:
                msg = await self.queue.get()
                await self._write(msg)
        except asyncio.CancelledError:
            # flush remaining messages
            while not self.queue.empty():
                msg = self.queue.get_nowait()
                self._write_sync(msg)

    async def _write(self, msg: str) -> None:
        sys.stdout.write(msg + "\n")
        await asyncio.sleep(0)  # yield control to loop

    def _write_sync(self, msg: str) -> None:
        sys.stdout.write(msg + "\n")



class LoggerMeta(ABCMeta):
    """
    A metaclass that automatically adds a `logger` field to abstract classes (child's elso have).
    The `logger` field is an instance of logging.Logger with the name of the class module.
    """
    def __new__(mcs, name: str, bases: tuple, namespace: dict[str, Any], **kwargs: Any) -> type:
        logger_name = f"{namespace.get('__module__')}.{name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)


        if not any(isinstance(h, AsyncHandler) for h in logger.handlers):
            handler = AsyncHandler()
            logger.addHandler(handler)

        namespace['logger'] = logger

        return super().__new__(mcs, name, bases, namespace, **kwargs)


def logging_method_exception(exception_types: type[Exception] | tuple[type[Exception]]):
    """
    decorator used for methods, need attr cls.logger
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self_or_cls, *args, **kwargs):
            logger: logging.Logger | None = None
            if hasattr(self_or_cls, 'logger'):
                logger = self_or_cls.logger
            elif hasattr(self_or_cls.__class__, 'logger'):
                logger = self_or_cls.__class__.logger
            try:
                return func(self_or_cls, *args, **kwargs)
            except exception_types as e:
                if logger:
                    logger.exception(e)
                raise e
        return wrapper

    return decorator



