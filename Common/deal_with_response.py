"""
响应处理 — 附加到 Allure 报告 + 控制台输出（与报告同格式）
性能优化：
- 仅在 allure listener 存活时才做 attach（普通调试运行零开销）
- 响应体截断到 2KB 避免大 JSON 拖慢报告
"""
import json
import allure
from Common.perf import format_duration
from Common.logger import log

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


# ANSI 颜色：200 天空蓝，非 200 橙色
_COLOR_SKY_BLUE = "\033[96m"   # 天空蓝/亮青
_COLOR_ORANGE = "\033[38;5;208m"  # 橙色 (256色)
_COLOR_RESET = "\033[0m"


def _log_to_console(request_url, request_method, request_headers, data, status_code, response_time, body):
    """控制台输出请求/响应信息，格式与报告一致；状态码 200 天空蓝，非 200 橙色"""
    sep = "-" * 80
    status_line = f"状态码: {status_code}"
    if status_code == 200:
        status_line = f"{_COLOR_SKY_BLUE}{status_line}{_COLOR_RESET}"
    else:
        status_line = f"{_COLOR_ORANGE}{status_line}{_COLOR_RESET}"
    lines = [
        sep,
        f"请求的URL: {request_url}",
        f"请求的方法: {request_method}",
        f"请求的Headers: {request_headers or {}}",
        f"入参报文: {data or ''}",
        sep,
        status_line,
        f"响应时间: {response_time}",
        f"响应报文:\n{body}",
        sep,
    ]
    log.info("\n" + "\n".join(lines))


def deal_with_res(data, res, request_url, request_method, request_headers, response_time):
    try:
        status_code = getattr(res, "status_code", None) or getattr(res, "status", None)
        if hasattr(res, "text"):
            body = res.text
        elif hasattr(res, "data"):
            body = res.data.decode("utf-8") if isinstance(res.data, bytes) else str(res.data)
        else:
            body = ""

        if len(body) > MAX_BODY_LEN:
            body = body[:MAX_BODY_LEN] + f"\n... (截断，原始 {len(body)} 字符)"

        # 控制台输出（与报告同格式）
        _log_to_console(
            request_url, request_method, request_headers, data,
            status_code, format_duration(response_time), body
        )

        # Allure 报告
        if not _is_allure_active():
            return

        text_type = allure.attachment_type.TEXT
        allure.attach(request_url, "请求的URL", text_type)
        allure.attach(request_method, "请求的方法", text_type)
        allure.attach(str(request_headers) if request_headers else "{}", "请求的Headers", text_type)
        allure.attach(str(data) if data else "", "入参报文", text_type)
        allure.attach(format_duration(response_time), "响应时间", text_type)
        allure.attach(str(status_code), "状态码", text_type)

        try:
            json.loads(body)
            allure.attach(body, "响应报文", allure.attachment_type.JSON)
        except (ValueError, TypeError):
            allure.attach(body, "响应报文", text_type)

    except Exception:
        pass
