"""
Utils package
包含各种工具函数
"""

# 从上层的utils.py导入函数，保持向后兼容
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta

# 北京时间时区（UTC+8）
BEIJING_TZ_OFFSET = timedelta(hours=8)

def get_beijing_time():
    """获取当前北京时间"""
    return datetime.utcnow() + BEIJING_TZ_OFFSET

# 导出函数
__all__ = ['get_beijing_time']

