import os
from typing import List, Dict

import requests

from Common.commom_requests import Requests


def get_mime_type(filename: str) -> str:
    """
    根据文件名获取 MIME 类型
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime'
    }
    return mime_types.get(ext, 'application/octet-stream')



