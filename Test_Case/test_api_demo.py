"""
数据驱动测试示例
从 YAML 文件读取测试数据，自动生成多条用例
"""
import os
import pytest
import allure
from Common.assertions import assert_response
from Config.config import Config
from Utils.Read_yaml_json import YamlReader

CASES = YamlReader(os.path.join(Config.Datas_path, "test_api_data.yaml")).read()


def _build_login_body(case):
    """根据 case 构建登录请求体，username 映射为 emailName"""
    body = {"isFirebaseEmail": "0"}
    if "username" in case:
        body["emailName"] = case["username"]
    if "password" in case:
        body["password"] = case["password"]
    return body


@allure.epic("接口测试")
@allure.feature("数据驱动示例")
class TestApiDataDriven:

    @pytest.mark.parametrize("case", CASES, ids=[c["case_name"] for c in CASES])
    @allure.severity(allure.severity_level.NORMAL)
    def test_api_with_data(self, http, case):
        """根据 YAML 数据驱动执行接口测试（登录接口无需 token，用 http）"""
        allure.dynamic.title(case["case_name"])
        method = case["method"].upper()
        path = case["path"]
        body = _build_login_body(case)

        if method == "POST":
            resp = http.post(path, json=body)
        else:
            pytest.skip(f"暂不支持 {method} 方法")
        assert case.get('msg') == resp.json().get('msg')
