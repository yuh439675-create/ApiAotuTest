from Common.common_requests import Requests
from Common.yaml_config import GetConfig


def login(user):
    """
    封装登录接口
    :param user: yaml 文件里账号密码的用户名称
    :return: requests.Response 对象（支持 .json()）

    配置说明（Login.yaml 的 user.xxx 下）:
    - 必填: username, password
    - 可选: 其他字段会原样合并到请求体
    """
    cfg = GetConfig()
    u = cfg.get_user_config(user)

    # 基础字段（username 映射为 emailName）
    data = {
        "emailName": u["username"],
        "password": u["password"],
        "isFirebaseEmail": "0",
    }

    # 合并用户配置中的其他字段
    for k, v in u.items():
        if k not in ("username", "password") and v is not None:
            data[k] = v

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    login_path = cfg.get_login_config()["path"]
    return Requests().post(login_path, headers=headers, json=data)


if __name__ == "__main__":
    resp = login("yhb")
    print(resp.status_code)
    print(resp.json())
