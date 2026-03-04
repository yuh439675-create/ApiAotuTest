"""
统一日志模块，项目中统一使用 get_logger() 获取 logger
- 控制台输出 INFO 及以上
- 文件输出 DEBUG 及以上，按天轮转
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from Config.config import Config

_loggers = {}


def get_logger(name="api_test"):
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件（按天轮转，保留 30 天）
    os.makedirs(Config.Logs_path, exist_ok=True)
    log_file = os.path.join(Config.Logs_path, f"{name}.log")
    fh = TimedRotatingFileHandler(log_file, when="midnight", backupCount=30, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    _loggers[name] = logger
    return logger


log = get_logger()
