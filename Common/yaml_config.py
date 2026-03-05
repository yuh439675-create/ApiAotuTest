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
        """返回 (username, password, code)，code 可选"""
        try:
            u = self.env["user"][user]
            code = u.get("code", "")
            return u["username"], u["password"], code
        except KeyError:
            raise KeyError(f"配置文件中未找到用户 '{user}' 的信息")

    def get_user_config(self, user):
        """
        返回用户完整配置，支持自由扩展字段。
        必填: username, password
        可选: code, captcha 或任意其他字段，按需配置即可
        """
        try:
            return dict(self.env["user"][user])
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

    def get_login_config(self):
        """
        获取登录相关配置
        返回: {
            "path": 登录接口路径,
            "token_field": token 在响应中的字段路径（支持 . 分隔的嵌套路径）
        }
        """
        login_cfg = self.env.get("login", {})
        return {
            "path": login_cfg.get("path", "sqx_fast/app/Login/emailLogin"),
            "token_field": login_cfg.get("token_field", "data.token"),
        }


if __name__ == "__main__":
    c1 = GetConfig()
    c2 = GetConfig()
    assert c1 is c2, "单例校验失败"
    print("单例OK:", c1.get_url())
