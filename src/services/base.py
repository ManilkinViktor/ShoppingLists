from logging import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL


from core.logger import LoggerMeta
from database.uow import UnitOfWork

class BaseService(metaclass=LoggerMeta):
    logger: Logger

    def __init__(self, uow: UnitOfWork):
        self.uow: UnitOfWork = uow

    # methods for logging after commit

    def _log_debug(self, msg: str, *args, **kwargs):
        self.uow.log(self.logger, DEBUG, msg, *args, **kwargs)

    def _log_info(self, msg: str, *args, **kwargs):
        self.uow.log(self.logger, INFO, msg, *args, **kwargs)

    def _log_warning(self, msg: str, *args, **kwargs):
        self.uow.log(self.logger, WARNING, msg, *args, **kwargs)

    def _log_error(self, msg: str, *args, **kwargs):
        self.uow.log(self.logger, ERROR, msg, *args, **kwargs)

    def _log_critical(self, msg: str, *args, **kwargs):
        self.uow.log(self.logger, CRITICAL, msg, *args, **kwargs)