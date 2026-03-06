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


# ANSI 颜色（五颜六色）
_COLOR_RESET = "\033[0m"
_C = {
    "sep": "\033[97m",      # 白色分隔线
    "url": "\033[96m",      # 亮青 - 请求URL
    "method": "\033[92m",   # 亮绿 - 请求方法
    "headers": "\033[93m",  # 亮黄 - Headers
    "params": "\033[94m",   # 亮蓝 - 入参
    "status_ok": "\033[96m",   # 亮青 - 状态码 200
    "status_err": "\033[38;5;208m",  # 橙色 - 状态码非 200
    "time": "\033[95m",     # 亮紫 - 响应时间
    "body": "\033[33m",     # 黄色 - 响应报文
}


def _log_to_console(request_url, request_method, request_headers, data, status_code, response_time, body):
    """控制台输出请求/响应信息，每行不同颜色（五颜六色）"""
    sep = f"{_C['sep']}{'-' * 80}{_COLOR_RESET}"
    sc = _C["status_ok"] if status_code == 200 else _C["status_err"]
    lines = [
        sep,
        f"{_C['url']}请求的URL: {request_url}{_COLOR_RESET}",
        f"{_C['method']}请求的方法: {request_method}{_COLOR_RESET}",
        f"{_C['headers']}请求的Headers: {request_headers or {}}{_COLOR_RESET}",
        f"{_C['params']}入参报文: {data or ''}{_COLOR_RESET}",
        f"{sc}状态码: {status_code}{_COLOR_RESET}",
        f"{_C['time']}响应时间: {response_time}{_COLOR_RESET}",
        f"{_C['body']}响应报文:\n{body}{_COLOR_RESET}",
        sep,
    ]
    log.info("\n\n\n" + "\n".join(lines))


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
