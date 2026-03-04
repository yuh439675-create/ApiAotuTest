"""
登录接口测试用例示例
演示框架的标准用法：fixture 注入、数据驱动、断言工具、Allure 标签
"""
import json
import os
import pytest
import allure
from Common.login import login
from Common.common_requests import Requests, AuthClient
from Common.assertions import assert_response
from Config.config import Config


# 读取测试数据
def load_test_data():
    path = os.path.join(Config.Datas_path, "test_login.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


TEST_DATA = load_test_data()


@allure.epic("用户管理")
@allure.feature("登录模块")
class TestLogin:

    @allure.story("正常登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("使用正确账号密码登录")
    def test_login_success(self, token):
        """验证正常登录流程，能获取到 token"""
        data = TEST_DATA["test_login_success"]
        resp = login(data["user"])

        assert_response(resp) \
            .status_ok() \
            .json_field_exists(data["expect_field"]) \
            .log_result("正常登录")

        # 同时验证 token fixture 能正常工作
        t = token(data["user"])
        assert t is not None and len(t) > 0

    @allure.story("异常登录")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("使用错误密码登录")
    def test_login_wrong_password(self):
        """验证错误密码登录时的响应"""
        data = TEST_DATA["test_login_wrong_password"]
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        resp = Requests().post("sys/login", headers=headers, json=data["data"])

        assert_response(resp) \
            .status_ok() \
            .log_result("错误密码登录")


@allure.epic("用户管理")
@allure.feature("登录模块")
class TestTokenManagement:

    @allure.story("Token 管理")
    @allure.title("Token 缓存与复用验证")
    def test_token_cache(self, token):
        """验证多次获取同一用户 token 返回相同值（缓存生效）"""
        t1 = token("yhb")
        t2 = token("yhb")
        assert t1 == t2, "同一用户的 token 应该来自缓存"

    @allure.story("Token 管理")
    @allure.title("Token 用于认证接口")
    def test_authenticated_request(self, api):
        """验证携带 token 的 API 客户端能正常发起请求"""
        client = api("yhb")
        assert isinstance(client, AuthClient)
        assert client._auth_headers.get("token")
