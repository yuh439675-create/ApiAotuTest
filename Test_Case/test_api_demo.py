"""
数据驱动测试示例
从 YAML 文件读取测试数据，自动生成多条用例
"""
import os
import yaml
import pytest
import allure
from Common.assertions import assert_response
from Config.config import Config


def load_yaml_cases():
    path = os.path.join(Config.Datas_path, "test_api_data.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CASES = load_yaml_cases()


@allure.epic("接口测试")
@allure.feature("数据驱动示例")
class TestApiDataDriven:

    @pytest.mark.parametrize(
        "case",
        CASES,
        ids=[c["case_name"] for c in CASES],
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_api_with_data(self, api, case):
        """根据 YAML 数据驱动执行接口测试"""
        allure.dynamic.title(case["case_name"])
        client = api("yhb")

        method = case["method"].upper()
        if method == "GET":
            resp = client.get(case["path"], params=case.get("params"))
        elif method == "POST":
            resp = client.post(case["path"], json=case.get("body"))
        else:
            pytest.skip(f"暂不支持 {method} 方法")

        assert_response(resp) \
            .status_is(case["expect_status"]) \
            .log_result(case["case_name"])
