
import logging
import sys
import queue
from logging.handlers import QueueHandler, QueueListener
from abc import ABCMeta
from functools import wraps
from typing import Any, Callable



# --- Colorized StreamHandler for QueueListener ---
class ColoredFormatter(logging.Formatter):
    COLOR_MAP = {
        logging.DEBUG: '\033[0m',
        logging.INFO: '\033[0m',
        logging.WARNING: '\033[33m',
        logging.ERROR: '\033[31m',
        logging.CRITICAL: '\033[31m',
    }
    COLOR_RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        color = self.COLOR_MAP.get(record.levelno, self.COLOR_RESET)
        if color != self.COLOR_RESET:
            return f"{color}{msg}{self.COLOR_RESET}"
        return msg

def get_colored_stream_handler() -> logging.Handler:
    fmt = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(fmt, datefmt=datefmt))
    return handler

# --- QueueHandler/QueueListener setup ---
_log_queue = queue.Queue(-1)
_stream_handler = get_colored_stream_handler()
_queue_listener = QueueListener(_log_queue, _stream_handler, respect_handler_level=True)
_queue_listener.start()

def get_queue_handler() -> logging.Handler:
    return QueueHandler(_log_queue)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False
    if not any(isinstance(h, QueueHandler) for h in logger.handlers):
        logger.addHandler(get_queue_handler())
    return logger



class LoggerMeta(ABCMeta):
    """
    A metaclass that automatically adds a `logger` field to abstract classes (child's also have).
    The `logger` field is an instance of logging.Logger with the name of the class module.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict[str, Any], **kwargs: Any) -> type:
        logger_name = f"{namespace.get('__module__')}.{name}"
        logger = get_logger(logger_name)
        namespace['logger'] = logger

        return super().__new__(mcs, name, bases, namespace, **kwargs)


def logging_method_exception(
        exception_types: type[Exception] | tuple[type[Exception]],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    decorator used for methods, need attr cls.logger
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self_or_cls: Any, *args: Any, **kwargs: Any) -> Any:
            logger: logging.Logger | None = None
            if hasattr(self_or_cls, 'logger'):
                logger = self_or_cls.logger
            elif hasattr(self_or_cls.__class__, 'logger'):
                logger = self_or_cls.__class__.logger
            try:
                return func(self_or_cls, *args, **kwargs)
            except exception_types as error:
                if logger:
                    logger.exception(error)
                raise

        return wrapper

    return decorator
