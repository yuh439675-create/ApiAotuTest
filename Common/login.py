from Common.common_requests import Requests
from Common.yaml_config import GetConfig


# 配置类字段，不入请求体
_BODY_SKIP_KEYS = ("username", "password", "path", "token_field", "username_key", "password_key", "url", "base_url", "emailName")


def login(user):
    """
    封装登录接口
    :param user: yaml 文件里账号密码的用户名称
    :return: requests.Response 对象（支持 .json()）

    配置说明（Login.yaml 的 user.xxx 下）:
    - 必填: username, password
    - 可选: username_key（用户名字段名，默认 emailName，后管常用 username）
    - 可选: password_key（密码字段名，默认 password）
    - 可选: adminType, captcha, uuid 等任意字段，会原样合并到请求体
    """
    cfg = GetConfig()
    u = cfg.get_user_config(user)

    username_key = u.get("username_key", "emailName")
    password_key = u.get("password_key", "password")
    username_value = u.get("username") or u.get("emailName")
    if username_value is None:
        raise ValueError(f"user '{user}' 必须配置 username 或 emailName")
    data = {username_key: username_value, password_key: u["password"]}
    if username_key == "emailName":
        data["isFirebaseEmail"] = "0"

    for k, v in u.items():
        if k not in _BODY_SKIP_KEYS and v is not None:
            data[k] = v

    # 动态字段（captcha、uuid 等）覆盖静态配置
    try:
        from Common.dynamic_login import get_dynamic_login_fields

        def _fetch_extra():
            return get_dynamic_login_fields(user)

        # Playwright Sync API 不能在 asyncio 循环中运行，需在新线程执行
        try:
            import asyncio
            asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                extra = ex.submit(_fetch_extra).result(timeout=120)
        except RuntimeError:
            extra = _fetch_extra()

        if extra:
            data.update(extra)
    except ImportError:
        pass

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    login_cfg = cfg.get_user_login_config(user)
    return Requests().post(login_cfg["path"], headers=headers, json=data)


if __name__ == "__main__":
    resp = login("yhb")
    print(resp.status_code)
    print(resp.json())
