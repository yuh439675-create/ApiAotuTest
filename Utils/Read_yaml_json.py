# utils/Read_yaml.py
import os
import yaml
from Config.config import Config

import yaml
import os
from typing import Dict, List, Optional, Union
from pathlib import Path


class YamlReader:
    """YAML 文件读取器，支持路径处理和错误处理"""

    def __init__(self, filename: str):
        """
        初始化 YAML 读取器

        Args:
            filename: YAML 文件路径
        """
        self.filepath = Path(filename).resolve()
        self._validate_file()

    def _validate_file(self) -> None:
        """验证文件是否存在且可读"""
        if not self.filepath.exists():
            raise FileNotFoundError(f"文件不存在: {self.filepath}")

        if not self.filepath.is_file():
            raise IsADirectoryError(f"不是文件: {self.filepath}")

        if not os.access(self.filepath, os.R_OK):
            raise PermissionError(f"没有读取权限: {self.filepath}")

    def read(self) -> Union[Dict, List]:
        """
        读取并解析 YAML 文件

        Returns:
            解析后的 YAML 数据
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 格式错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"读取文件时发生错误: {e}") from e

    def read_with_processing(self) -> Union[Dict, List]:
        """
        读取 YAML 文件并处理 URL 和文件路径

        Returns:
            处理后的 YAML 数据
        """
        data = self.read()

        # 确保是列表类型
        if not isinstance(data, list):
            data = [data]

        processed_data = []
        for item in data:
            if not isinstance(item, dict):
                processed_data.append(item)
                continue

            # 处理 URL 地址
            if 'url地址' in item and item['url地址']:
                item['url地址'] = f"{Config.url}{item['url地址']}"

            # 处理文件路径
            if 'files' in item and item['files']:
                item['files'] = os.path.join(Config.test_files_dir, item['files'])

            processed_data.append(item)

        return processed_data


#


if __name__ == '__main__':
    try:
        yaml_path = os.path.join(Config.Datas_path, 'test_api_data.yaml')
        reader = YamlReader(yaml_path)

        # 直接读取
        raw_data = reader.read()
        print("原始数据:", raw_data)

        # 读取并处理
        processed_data = reader.read_with_processing()
        print("处理后数据:", processed_data)

    except Exception as e:
        print(f"错误: {e}")
