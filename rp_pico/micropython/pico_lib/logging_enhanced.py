import json
import os
import utime

from . import logging
from .logging_handlers import RotatingFileHandler
from .settings_base import Settings_Base

class _Console_Logger_Settings:
    def __init__(self) -> None:
        self.enabled = True
        self.default_log_level = 'INFO'
        self.log_levels_for_modules = {}

class _File_Logger_Settings:
    def __init__(self) -> None:
        self.enabled = True
        self.dirname = 'log'
        self.max_bytes = 10000
        self.backup_count = 2
        self.default_log_level = 'WARNING'
        self.log_levels_for_modules = {}

class _Settings(Settings_Base):
    def __init__(self) -> None:
        super().__init__()
        self.console_logger = _Console_Logger_Settings()
        self.file_logger = _File_Logger_Settings()

class Formatter_Enhanced(logging.Formatter):
    '''Override formatter from base class to customize date/time format.'''
    def formatTime(self, record, datefmt=None):
        assert datefmt is None  # datefmt is not supported
        ct = utime.localtime(record.created)
        return "{0}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*ct)

class Logger_Enhanced(logging.Logger):
    '''Enhancements for logging'''
    _LOGGER_SETTINGS_FILE = 'config/log_settings.json'

    _settings = _Settings()
    _settings.load(__name__, _LOGGER_SETTINGS_FILE)
    print(f'Logger settings read from {_LOGGER_SETTINGS_FILE};')
    print(f'  console_logger.enabled = {_settings.console_logger.enabled}')
    print(f'  console_logger.default_log_level = {_settings.console_logger.default_log_level}')
    print(f'  console_logger.log_levels_for_modules = {_settings.console_logger.log_levels_for_modules}')
    print(f'  file_logger.enabled = {_settings.file_logger.enabled}')
    print(f'  file_logger.dirname = {_settings.file_logger.dirname}')
    print(f'  file_logger.max_bytes = {_settings.file_logger.max_bytes}')
    print(f'  file_logger.backup_count = {_settings.file_logger.backup_count}')
    print(f'  file_logger.default_log_level = {_settings.file_logger.default_log_level}')
    print(f'  file_logger.log_levels_for_modules = {_settings.file_logger.log_levels_for_modules}')

    _console_handler = logging.StreamHandler()
    console_formatter = Formatter_Enhanced('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    _console_handler.setFormatter(console_formatter)

    logfile_path = _settings.file_logger.dirname + '/log.log'
    _file_handler = RotatingFileHandler(logfile_path, _settings.file_logger.max_bytes, _settings.file_logger.backup_count)
    file_formatter = Formatter_Enhanced('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    _file_handler.setFormatter(file_formatter)

    def __init__(self, name):
        # Use self._console_level and self._file_level instead of self.level from base class.
        self._console_level = logging.NOTSET
        self._file_level = logging.NOTSET
        super().__init__(name)

    def log(self, level, msg, *args):
        '''Overrides same method in base class (logging.Logger).'''
        if self._settings.console_logger.enabled:
            self._log_console(level, msg, *args)
        if self._settings.file_logger.enabled:
            self._log_file(level, msg, *args)

    def _log_console(self, level, msg, *args):
        dest = self
        while dest._console_level == logging.NOTSET and dest.parent:
            dest = dest.parent
        if level >= dest._console_level:
            record = logging.LogRecord(
                self.name, level, None, None, msg, args, None, None, None
            )
            self._console_handler.emit(record)

    def _log_file(self, level, msg, *args):
        dest = self
        while dest._file_level == logging.NOTSET and dest.parent:
            dest = dest.parent
        if level >= dest._file_level:
            record = logging.LogRecord(
                self.name, level, None, None, msg, args, None, None, None
            )
            self._file_handler.emit(record)

    @classmethod
    def get_logger_for_module(cls, module_name):
        '''Get logger for module and configure it according to settings-logger.json.
        
        REMARK: 'level' in base class logging.Logger is replaced by '_console_level' and '_file_level' in this class.
        Don't use setLevel(level) from base class logging.Logger!
        '''
        logger = cls._getLogger(module_name)
        if module_name in cls._settings.console_logger.log_levels_for_modules:
            logger._console_level = cls._getLevelValue(cls._settings.console_logger.log_levels_for_modules[module_name])
        else:
            logger._console_level = cls._getLevelValue(cls._settings.console_logger.default_log_level)
            print(f"WARNING: Minimal console log level for module '{module_name}' not configured, using '{cls._settings.console_logger.default_log_level}'.")
        if logger._console_level not in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG):
            logger._console_level = logging.INFO
            print(f"WARNING: Unknown console log level defined for module '{module_name}', using 'INFO'.")

        if module_name in cls._settings.file_logger.log_levels_for_modules:
            logger._file_level = cls._getLevelValue(cls._settings.file_logger.log_levels_for_modules[module_name])
        else:
            logger._file_level = cls._getLevelValue(cls._settings.file_logger.default_log_level)
            print(f"WARNING: Minimal file log level for module '{module_name}' not configured, using '{cls._settings.file_logger.default_log_level}'.")
        if logger._file_level not in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG):
            logger._file_level = logging.WARNING
            print(f"WARNING: Unknown file log level defined for module '{module_name}', using 'WARNING'.")

        logger.info(f"Configured logger for module '{module_name}': log level for console/file = {logging.getLevelName(logger._console_level)}/{logging.getLevelName(logger._file_level)}.")
        return logger

    @classmethod
    def _getLogger(cls, name=None):
        '''Copied from logging.getLogger(), but returns Enhanced_Logger.'''
        if name is None:
            name = "root"
        if name in logging._loggers:
            return logging._loggers[name]
        logger = Logger_Enhanced(name)
        # For now, we have shallow hierarchy, where parent of each logger is root.
        logger.parent = logging.root
        logging._loggers[name] = logger
        return logger

    @classmethod
    def _getLevelValue(cls, level_name: str):
        level_value = getattr(logging, level_name.upper(), None)
        if not isinstance(level_value, int):
            raise ValueError('Invalid log level: %s' % level_name)
        return level_value

    @classmethod
    def _create_directory(cls, dirname):
        try:
            os.mkdir(dirname)
        except OSError as err:
            pass # ignore error if directory already exists
