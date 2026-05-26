import logging
import os
from logging.handlers import RotatingFileHandler
import sys

# 确保日志目录存在
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加handler
    if not logger.handlers:
        # 文件处理器
        log_file = os.path.join(LOG_DIR, "app.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024, # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 控制台处理器
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    return logger

# 默认导出
logger = setup_logger("meeting_analyzer")
