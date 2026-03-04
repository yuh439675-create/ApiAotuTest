from Common.common_requests import Requests
from Common.yaml_config import GetConfig


def login(user):
    """
    封装登录接口
    :param user: yaml 文件里账号密码的用户名称
    :return: requests.Response 对象（支持 .json()）
    """
    username, password, code = GetConfig().get_username_password(user)

    data = {
        "username": username,
        "password": password,
        "captcha": code,
        "uuid": "d3785d19-d127-47c6-8f5e-b0c19c2ef91f",
        "adminType": 1,
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    return Requests().post("sys/login", headers=headers, json=data)


if __name__ == "__main__":
    resp = login("yhb")
    print(resp.status_code)
    print(resp.json())
