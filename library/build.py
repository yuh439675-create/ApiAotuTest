# -*- coding: utf-8 -*-
"""BuildInLibrary - 参数替换等工具（BasePage 依赖）"""


class BuildInLibrary:
    def repalce_parameter(self, value):
        """参数替换，支持 ${var} 等占位符。当前为透传，可按需扩展。"""
        return value if value is not None else ""
