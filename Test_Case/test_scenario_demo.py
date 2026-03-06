"""
业务流程测试（场景测试）示例

做法：在一个 test 里按「业务顺序」连续调用多个接口，上一步的返回值（token、id 等）
作为下一步的入参，用 allure.step 拆成多步，报告里会按步骤展示。

运行方式（与单接口用例相同）：
  python Runner.py Test_Case/test_scenario_demo.py
  python Runner.py -k scenario   # 只跑场景用例
"""
import pytest
import allure
from Common.assertions import assert_response
from Common.mysql_operate import MysqlOperate
db = MysqlOperate()
# 之后所有操作都用 db 调用


# 把需要登录后的接口路径集中配置，便于维护（也可放到 Config/xxx.yaml）
class ScenarioPaths:
    """场景中用到的接口路径（请按项目实际修改）"""
    # 示例：登录后拉取用户/业务数据
    USER_OR_INFO = "sqx_fast/app/user/selectUserById"   # 替换为真实「获取用户信息」等接口
    # 若有「依赖上一步结果」的接口，例如用token查询剩下的lol数量
    ORDER_LIST = "sqx_fast/app/cash/getCryptoBalance"      # 替换为真实接口
    # 调用提现接口
    creditsExchangeToLolWithdraw = 'sqx_fast/app/integral/creditsExchangeToLolWithdraw'


@allure.epic("业务流程测试")
@allure.feature("场景示例")
class TestScenarioDemo:

    @allure.story("最小场景")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("场景：登录并验证 token 可用于请求（不依赖其他接口）")
    def test_login_and_use_token(self, api):
        """最小可运行场景：仅「登录 → 用 token 发一次请求」，无其他接口依赖。"""
        with allure.step("1. 获取已登录客户端（内部会登录或读缓存）"):
            client = api("yhb")
            assert client._auth_headers.get("token"), "应有 token"

        with allure.step("2. 用 token 请求需认证接口"):
            resp = client.get(ScenarioPaths.USER_OR_INFO)
            assert resp.status_code != 500, f"服务异常: {resp.text[:200]}"
            if resp.status_code == 200:
                assert_response(resp).status_ok()
            else:
                pytest.skip(f"当前接口返回 {resp.status_code}，请将 ScenarioPaths 改为真实路径后再跑")

    @allure.story("登录后连续调用多个需认证接口")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("场景：登录 → 获取用户信息 → 依赖结果调用下一接口")
    def test_login_then_chain_apis(self, http, api):
        """
        典型场景：先拿到已登录客户端，再依次调用多个依赖 token 的接口，
        中间结果（如 user_id）传给后续请求。
        """
        client = api("yhb")
        # ---------- 步骤 1：调用需要登录的接口 A ----------
        with allure.step("1. 调用需认证接口（如获取用户信息）"):
            resp1 = client.get(ScenarioPaths.USER_OR_INFO)
            assert_response(resp1).status_ok()
            body1 = resp1.json()
            self.user_id = body1.get('data')['userId']
            assert resp1.json().get('code') == 0

        # ---------- 步骤 2：用上一步结果调用接口 ----------
        with allure.step("2. 用上一步结果调用下一接口（如订单列表）"):
            resp2 = client.get(ScenarioPaths.ORDER_LIST)
            assert_response(resp2).status_ok()
            assert resp2.json().get('code') == 0



        # ---------- 步骤 3：提现接口 ----------
        with allure.step("3. 提现接口"):
            resp3 = client.post(ScenarioPaths.creditsExchangeToLolWithdraw, json={
                'address': "0xb738c553a56576a085aa9e33d827dc4b78310521",
                'chainId': '66',
                'integral': 2000
            })
            assert_response(resp3).status_ok()
            assert resp3.json().get('code') == 0





#     @allure.story("纯流程串联")
#     @allure.severity(allure.severity_level.NORMAL)
#     @allure.title("场景：仅验证登录后能连续访问多个接口")
#     def test_multi_step_with_same_client(self, api):
#         """不依赖中间结果时：同一 client 连续调多个接口即可。"""
#         client = api("yhb")
#
#         with allure.step("请求接口 A"):
#             r1 = client.get(ScenarioPaths.USER_OR_INFO)
#             assert_response(r1).status_ok()
#
#         with allure.step("请求接口 B（同一 token）"):
#             r2 = client.get(ScenarioPaths.ORDER_LIST)
#             assert_response(r2).status_ok()
#
#
# # 若你有「先登录拿 token，再手动拼请求」的习惯，可以这样写（与上面二选一即可）
# @allure.epic("业务流程测试")
# @allure.feature("场景示例")
# class TestScenarioWithLoginResponse:
#
#     @allure.story("显式登录并复用登录结果")
#     @allure.severity(allure.severity_level.NORMAL)
#     @allure.title("场景：登录 → 从响应取 token/uid → 调后续接口")
#     def test_login_then_use_response(self, http):
#         """适合：第一步必须是登录，且需要从登录响应里拿不止 token 的字段时。"""
#         from Common.login import login
#
#         with allure.step("1. 登录并校验"):
#             resp_login = login("yhb")
#             assert_response(resp_login).status_ok().json_field_exists("token")
#             data = resp_login.json()
#             token = data.get("token")
#             # 若有 uid、nickname 等也可一并取出
#             uid = data.get("data", {}).get("uid") or data.get("uid")
#
#         with allure.step("2. 用 token 调需认证接口"):
#             from Common.common_requests import AuthClient
#             client = AuthClient(token=token)
#             r = client.get(ScenarioPaths.USER_OR_INFO)
#             assert_response(r).status_ok()
