"""
响应断言工具
性能优化：JSON body 延迟解析，仅在首次访问 JSON 字段时触发
"""
import allure
from Common.logger import log
from Common.perf import format_duration

_SENTINEL = object()


class ResponseAssert:
    """链式断言"""

    def __init__(self, response):
        self.resp = response
        self._body = _SENTINEL  # 延迟解析标记

    @property
    def body(self):
        if self._body is _SENTINEL:
            try:
                self._body = self.resp.json()
            except Exception:
                self._body = None
        return self._body

    # ── 状态码断言 ──

    def status_ok(self):
        assert self.resp.status_code == 200, (
            f"期望 200，实际 {self.resp.status_code}"
        )
        return self

    def status_is(self, code):
        assert self.resp.status_code == code, (
            f"期望 {code}，实际 {self.resp.status_code}"
        )
        return self

    # ── JSON 字段断言 ──

    def json_field_equals(self, field, expected):
        actual = self._nested(field)
        assert actual == expected, (
            f"'{field}' 期望 {expected!r}，实际 {actual!r}"
        )
        return self

    def json_field_exists(self, field):
        assert self._nested(field) is not None, f"'{field}' 不存在"
        return self

    def json_field_contains(self, field, sub):
        actual = self._nested(field)
        assert sub in str(actual), (
            f"'{field}' 值 {actual!r} 不包含 {sub!r}"
        )
        return self

    def json_list_not_empty(self, field):
        actual = self._nested(field)
        assert isinstance(actual, list) and actual, (
            f"'{field}' 应为非空列表，实际 {actual!r}"
        )
        return self

    def json_field_type(self, field, expected_type):
        actual = self._nested(field)
        assert isinstance(actual, expected_type), (
            f"'{field}' 期望类型 {expected_type.__name__}，实际 {type(actual).__name__}"
        )
        return self

    # ── 性能断言 ──

    def response_time_less_than(self, ms):
        elapsed = self.resp.elapsed.total_seconds() * 1000
        assert elapsed < ms, f"响应 {format_duration(elapsed)} 超过阈值 {format_duration(ms)}"
        return self

    # ── 工具方法 ──

    def _nested(self, path):
        """按 '.' 路径取值，支持数组索引"""
        if self.body is None:
            return None
        obj = self.body
        for key in path.split("."):
            if isinstance(obj, dict):
                obj = obj.get(key)
            elif isinstance(obj, list) and key.isdigit():
                idx = int(key)
                obj = obj[idx] if idx < len(obj) else None
            else:
                return None
            if obj is None:
                return None
        return obj

    def log_result(self, case_name=""):
        text = self.resp.text
        brief = text[:300] if len(text) > 300 else text
        log.info(f"[{case_name}] {self.resp.status_code} | {brief}")
        allure.attach(text, f"{case_name} 响应", allure.attachment_type.JSON)
        return self


def assert_response(response):
    return ResponseAssert(response)
