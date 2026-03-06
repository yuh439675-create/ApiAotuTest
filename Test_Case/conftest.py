import os

# 启用终端颜色（PyCharm / Runner 下 live log setup/teardown 金黄色）
os.environ.setdefault("PY_COLORS", "1")

import re
import json
import time
import logging
from typing import Callable
import pytest
import allure
from Common.login import login
from Common.common_requests import Requests, AuthClient
from Common.yaml_config import GetConfig
from Config.config import Config
from Common.perf import perf, format_duration

TOKEN_EXPIRE_SECONDS = 7200
logger = logging.getLogger("test")


def _get_nested_value(data, field_path):
    """
    根据 . 分隔的路径从嵌套字典中提取值
    例如: _get_nested_value({"data": {"token": "xxx"}}, "data.token") -> "xxx"
    """
    keys = field_path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit():
            value = value[int(key)]
        else:
            return None
        if value is None:
            return None
    return value


def _decode_unicode(s):
    """将字符串中的 \\uXXXX 转义还原为中文"""
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def pytest_configure(config):
    """live log setup/teardown 改为金黄色"""
    try:
        import _pytest.logging as _logging
        _orig_emit = _logging._LiveLoggingStreamHandler.emit

        def _emit_golden(self, record):
            from contextlib import nullcontext
            ctx = (
                self.capture_manager.global_and_fixture_disabled()
                if self.capture_manager else nullcontext()
            )
            with ctx:
                if not self._first_record_emitted:
                    self.stream.write("\n")
                    self._first_record_emitted = True
                elif self._when in ("teardown", "finish"):
                    if not self._test_outcome_written:
                        self._test_outcome_written = True
                        self.stream.write("\n")
                if not self._section_name_shown and self._when:
                    self.stream.section("live log " + self._when, sep="-", bold=True, yellow=True)
                    self._section_name_shown = True
                super(_logging._LiveLoggingStreamHandler, self).emit(record)

        _logging._LiveLoggingStreamHandler.emit = _emit_golden
    except Exception:
        pass


def pytest_collection_modifyitems(items):
    """pytest 收集完用例后，把 nodeid 里的 \\uXXXX 还原为中文"""
    for item in items:
        item._nodeid = _decode_unicode(item.nodeid)


@pytest.fixture(scope="session", autouse=True)
def setup_dirs():
    Config.ensure_dirs()


@pytest.fixture(scope="session")
def token():
    _cache = {}

    def _get_token(user):
        if user in _cache:
            return _cache[user]

        token_path = os.path.join(Config.Token_dir, f"{user}_token.json")

        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < TOKEN_EXPIRE_SECONDS:
                _cache[user] = data["token"]
                return _cache[user]

        resp = login(user)
        try:
            resp_json = resp.json()
        except Exception as e:
            logger.error("登录响应非 JSON，状态码: %s, 响应体: %s", resp.status_code, resp.text[:500] if resp.text else "(空)")
            raise ValueError(f"登录响应解析失败: {e}\n状态码: {resp.status_code}\n响应体: {resp.text[:500]}") from e

        # 从配置读取 token 字段路径（支持用户级 path/token_field）
        token_field = GetConfig().get_user_login_config(user)["token_field"]
        new_token = _get_nested_value(resp_json, token_field)

        if new_token is None:
            err_msg = (
                f"登录失败或 token 字段配置错误。\n"
                f"  状态码: {resp.status_code}\n"
                f"  配置的 token_field: {token_field}\n"
                f"  实际响应: {resp_json}"
            )
            logger.error(err_msg)
            print("\n" + "=" * 60 + "\n[登录失败] " + err_msg + "\n" + "=" * 60)
            raise ValueError(err_msg)

        with open(token_path, "w") as f:
            json.dump({"token": new_token, "timestamp": time.time()}, f)

        _cache[user] = new_token
        return new_token

    return _get_token


@pytest.fixture(scope="session")
def api(token) -> Callable[[str], AuthClient]:
    _clients = {}

    def _api(user) -> AuthClient:
        if user not in _clients:
            t = token(user)
            base_url = GetConfig().get_user_base_url(user)
            _clients[user] = AuthClient(token=t, base_url=base_url)
        return _clients[user]

    return _api


@pytest.fixture(scope="session")
def http() -> Requests:
    return Requests()


@pytest.fixture(autouse=True)
def _track_test_perf(request):
    """
    每条用例自动追踪性能：
    - 开始时重置用例级计数器
    - 结束后将该用例内所有接口耗时明细表 attach 到 Allure
    """
    perf.start_test()
    start = time.perf_counter()
    logger.info(f">> 开始: {request.node.nodeid}")

    yield

    total_ms = (time.perf_counter() - start) * 1000
    logger.info(f"<< 结束: {request.node.nodeid}  用例耗时: {format_duration(total_ms)}")

    # 生成该用例的接口耗时明细并 attach
    detail = perf.format_test_report()
    if detail:
        summary = f"用例总耗时: {format_duration(total_ms)}\n\n{detail}"
        allure.attach(summary, "接口性能明细", allure.attachment_type.TEXT)


def pytest_sessionfinish(session, exitstatus):
    """测试全部结束后：输出全局性能统计到日志 + Allure"""
    report = perf.report()
    if report != "无请求数据":
        logger.info(report)
        try:
            allure.attach(report, "全局接口性能统计", allure.attachment_type.TEXT)
        except Exception:
            pass
