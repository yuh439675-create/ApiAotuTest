"""
响应处理 — 附加到 Allure 报告
性能优化：
- 仅在 allure listener 存活时才做 attach（普通调试运行零开销）
- 响应体截断到 2KB 避免大 JSON 拖慢报告
"""
import allure
from Common.perf import format_duration
from allure_commons._allure import StepContext

_ALLURE_ACTIVE = None
MAX_BODY_LEN = 2048


def _is_allure_active():
    """检测当前是否在 allure 报告模式运行"""
    global _ALLURE_ACTIVE
    if _ALLURE_ACTIVE is not None:
        return _ALLURE_ACTIVE
    try:
        from allure_commons._core import plugin_manager
        _ALLURE_ACTIVE = bool(plugin_manager.list_name_plugin())
    except Exception:
        _ALLURE_ACTIVE = False
    return _ALLURE_ACTIVE


def deal_with_res(data, res, request_url, request_method, request_headers, response_time):
    if not _is_allure_active():
        return

    try:
        text_type = allure.attachment_type.TEXT
        allure.attach(request_url, "请求的URL", text_type)
        allure.attach(request_method, "请求的方法", text_type)
        allure.attach(str(request_headers) if request_headers else "{}", "请求的Headers", text_type)
        allure.attach(str(data) if data else "", "入参报文", text_type)
        allure.attach(format_duration(response_time), "响应时间", text_type)

        status_code = getattr(res, "status_code", None) or getattr(res, "status", None)
        allure.attach(str(status_code), "状态码", text_type)

        if hasattr(res, "text"):
            body = res.text
        elif hasattr(res, "data"):
            body = res.data.decode("utf-8") if isinstance(res.data, bytes) else str(res.data)
        else:
            body = ""

        if len(body) > MAX_BODY_LEN:
            body = body[:MAX_BODY_LEN] + f"\n... (截断，原始 {len(body)} 字符)"

        # 响应报文优先用 JSON 类型，便于 Allure 内联展示
        try:
            import json
            json.loads(body)
            allure.attach(body, "响应报文", allure.attachment_type.JSON)
        except (ValueError, TypeError):
            allure.attach(body, "响应报文", text_type)

    except Exception:
        pass
