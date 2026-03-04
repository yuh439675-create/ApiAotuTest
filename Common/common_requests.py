"""
统一 HTTP 请求封装
- 全局共享 Session（TCP 连接复用）
- 每个请求自动包裹 allure.step —— 报告里直接显示每个请求的耗时
- 用户级 AuthClient 隔离 headers
"""
import time
import threading
import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from Common.yaml_config import GetConfig
from Common.deal_with_response import deal_with_res
from Common.perf import perf

_session = None
_session_lock = threading.Lock()
_base_url = None


def _get_base_url():
    global _base_url
    if _base_url is None:
        _base_url = GetConfig().get_url()
    return _base_url


def get_session():
    global _session
    if _session is not None:
        return _session
    with _session_lock:
        if _session is None:
            s = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET", "POST", "PUT", "DELETE"],
            )
            adapter = HTTPAdapter(
                max_retries=retries,
                pool_connections=30,
                pool_maxsize=30,
            )
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            _session = s
    return _session


class Requests:
    def __init__(self, timeout=30):
        self.session = get_session()
        self.timeout = timeout
        self.base_url = _get_base_url()

    def _url(self, path):
        if path.startswith(("http://", "https://")):
            return path
        return self.base_url.rstrip("/") + "/" + path.lstrip("/")

    def _send(self, method, path, **kwargs):
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        req_data = kwargs.get("json") or kwargs.get("data") or kwargs.get("params")
        req_headers = kwargs.get("headers", {})

        step_title = f"[{method}] {path}"

        with allure.step(step_title):
            start = time.perf_counter()
            try:
                resp = self.session.request(method, url, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000

                perf.record(url, method, elapsed_ms)
                deal_with_res(req_data, resp, url, method, req_headers, elapsed_ms)

                allure.attach(
                    f"{elapsed_ms:.0f}ms (状态码: {resp.status_code})",
                    f"耗时 | {method} {path}",
                )
                return resp
            except requests.RequestException as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                allure.attach(f"请求失败 ({elapsed_ms:.0f}ms): {exc}", "请求异常")
                raise Exception(f"{method} 请求失败: {url} -> {exc}")

    def get(self, path, params=None, headers=None, **kw):
        return self._send("GET", path, params=params, headers=headers, **kw)

    def post(self, path, data=None, json=None, headers=None, files=None, **kw):
        return self._send("POST", path, data=data, json=json, headers=headers, files=files, **kw)

    def put(self, path, data=None, json=None, headers=None, **kw):
        return self._send("PUT", path, data=data, json=json, headers=headers, **kw)

    def delete(self, path, params=None, headers=None, **kw):
        return self._send("DELETE", path, params=params, headers=headers, **kw)

    get_request = get
    post_request = post


class AuthClient(Requests):
    def __init__(self, token, timeout=30, extra_headers=None):
        super().__init__(timeout=timeout)
        self._auth_headers = {
            "token": token,
            "Content-Type": "application/json",
        }
        if extra_headers:
            self._auth_headers.update(extra_headers)

    def _send(self, method, path, **kwargs):
        merged = dict(self._auth_headers)
        if kwargs.get("headers"):
            merged.update(kwargs["headers"])
        kwargs["headers"] = merged
        return super()._send(method, path, **kwargs)
