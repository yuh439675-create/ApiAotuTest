import os
import json
import time
import logging
import pytest
import allure
from Common.login import login
from Common.common_requests import Requests, AuthClient
from Config.config import Config
from Common.perf import perf

TOKEN_EXPIRE_SECONDS = 7200
logger = logging.getLogger("test")


def _display_nodeid(nodeid):
    """将 nodeid 中的 \\uXXXX 转义还原为中文，便于控制台阅读"""
    try:
        if "\\u" in nodeid:
            return nodeid.encode("utf-8").decode("unicode_escape")
    except Exception:
        pass
    return nodeid


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
        new_token = resp.json()["data"]["loginCode"]

        with open(token_path, "w") as f:
            json.dump({"token": new_token, "timestamp": time.time()}, f)

        _cache[user] = new_token
        return new_token

    return _get_token


@pytest.fixture(scope="session")
def api(token):
    _clients = {}

    def _api(user):
        if user not in _clients:
            t = token(user)
            _clients[user] = AuthClient(token=t)
        return _clients[user]

    return _api


@pytest.fixture(scope="session")
def http():
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
    logger.info(f">> 开始: {_display_nodeid(request.node.nodeid)}")

    yield

    total_ms = (time.perf_counter() - start) * 1000
    logger.info(f"<< 结束: {_display_nodeid(request.node.nodeid)}  用例耗时: {total_ms:.0f}ms")

    # 生成该用例的接口耗时明细并 attach
    detail = perf.format_test_report()
    if detail:
        summary = f"用例总耗时: {total_ms:.0f}ms\n\n{detail}"
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
