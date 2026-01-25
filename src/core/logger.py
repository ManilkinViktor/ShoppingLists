import logging
import sys
from functools import wraps
from typing import Any
from logging import Logger
import asyncio

from black.trans import Callable


class AsyncHandler(logging.Handler):
    """
    Async log handler that doesn't block the main thread.
    Sends messages to the console via asyncio.
    """

    COLOR_MAP = {
        logging.DEBUG: '\033[0m',
        logging.INFO: '\033[0m',
        logging.WARNING: '\033[33m',
        logging.ERROR: '\033[31m',
        logging.CRITICAL: '\033[31m',
    }
    COLOR_RESET = '\033[0m'

    def __init__(self):
        super().__init__()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.setFormatter(self._get_formatter())


    def _get_formatter(self) -> logging.Formatter:
        fmt = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'

        class ColoredFormatter(logging.Formatter):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.color_map = AsyncHandler.COLOR_MAP
                self.color_reset = AsyncHandler.COLOR_RESET

            def format(self, record: logging.LogRecord) -> str:
                log_msg = super().format(record)


                color = self.color_map.get(record.levelno, self.color_reset)

                if color != self.color_reset:
                    return f"{color}{log_msg}{self.color_reset}"
                else:
                    return log_msg

        return ColoredFormatter(fmt, datefmt=datefmt)

    def _try_get_loop(self) -> None:
        """Пытается получить текущий цикл событий."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def emit(self, record: logging.LogRecord) -> None:
        self._try_get_loop()
        try:
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._do_emit, record)
            else:
                self._do_emit_sync(record)
        except Exception as e:
            self.handle_emit_error(e, record)


    def _do_emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        print(msg, file=sys.stdout)

    def _do_emit_sync(self, record: logging.LogRecord) -> None:
        """Synchronous output (if the loop is not running)."""
        msg = self.format(record)
        print(f"[SYNC] {msg}", file=sys.stdout)

    @staticmethod
    def handle_emit_error(error: Exception, record: logging.LogRecord) -> None:
        try:
            error_msg = (
                f"[LOGGING ERROR] Failed to emit log record."
                f"!Logger: {record.name}, "
                f"!Level: {record.levelname}, "
                f"!Message: {record.getMessage()[:100]}..., "
                f"f!Exception: {type(error).__name__}: {error} "
            )
            print(error_msg, file=sys.stderr, flush=True)
        except Exception:
            sys.stderr.write("[LOGGING] Critical failure in error handling\n")



class LoggerMeta(type):
    """
    A metaclass that automatically adds a `logger` field to classes.
    The `logger` field is an instance of logging.Logger with the name of the class module.
    """
    def __new__(mcs, name: str, bases: tuple, namespace: dict[str, Any], **kwargs: Any) -> type:
        logger_name = namespace.get('__module__', '') + '.' + name
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)


        if not logger.handlers:
            handler = AsyncHandler()
            logger.addHandler(handler)

        namespace['logger'] = logger

        return super().__new__(mcs, name, bases, namespace, **kwargs)


def logging_method_exception(exception_types: type[Exception] | tuple[type[Exception]]):
    """
    decorator used for methods, need attr cls.logger
    :param exception_types:
    :return:
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







