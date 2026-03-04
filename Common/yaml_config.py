import yaml
import threading
from Config.config import Config

_instance = None
_lock = threading.Lock()


class GetConfig:
    """
    配置读取（单例），整个进程只读一次 YAML。
    多线程安全。
    """

    def __new__(cls):
        global _instance
        if _instance is not None:
            return _instance
        with _lock:
            if _instance is None:
                obj = super().__new__(cls)
                obj._load()
                _instance = obj
        return _instance

    def _load(self):
        path = Config.Login_yaml_path
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.env = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"配置文件 {path} 未找到，请复制 Login.yaml.example 为 Login.yaml"
            )
        except yaml.YAMLError as exc:
            raise ValueError(f"解析配置文件出错: {exc}")

    def reload(self):
        """强制重新加载配置（测试/调试用）"""
        self._load()

    def get_username_password(self, user):
        try:
            u = self.env["user"][user]
            return u["username"], u["password"], u["code"]
        except KeyError:
            raise KeyError(f"配置文件中未找到用户 '{user}' 的信息")

    def get_url(self):
        return self.env.get("url", "")

    def get_mysql_config(self):
        try:
            return self.env["mysql"]
        except KeyError:
            raise KeyError("配置文件中未找到 'mysql' 配置")

    def get_value(self, key, default=None):
        return self.env.get(key, default)


if __name__ == "__main__":
    c1 = GetConfig()
    c2 = GetConfig()
    assert c1 is c2, "单例校验失败"
    print("单例OK:", c1.get_url())
