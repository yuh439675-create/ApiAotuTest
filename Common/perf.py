"""
性能监控工具
- 全局维度：P50 / P90 / P99 / Max 统计
- 用例维度：每条用例内所有请求的耗时明细（自动附加到 Allure）
- 慢接口告警
"""
import time
import threading
import statistics
from Common.logger import log

SLOW_THRESHOLD_MS = 3000


def format_duration(ms):
    """将毫秒转为「X.X秒」格式，如 3700 -> 3.7秒"""
    if ms is None or ms < 0:
        return "0.0秒"
    sec = ms / 1000
    return f"{sec:.1f}秒"


class PerfCollector:
    """线程安全的性能收集器，支持全局 + 用例级双维度"""

    def __init__(self):
        self._global_data = {}          # {key: [ms, ...]}    全局汇总
        self._test_records = []         # [(method, url, ms)]  当前用例内的请求
        self._lock = threading.Lock()

    def record(self, url, method, elapsed_ms):
        key = f"{method} {url}"
        with self._lock:
            self._global_data.setdefault(key, []).append(elapsed_ms)
            self._test_records.append((method, url, elapsed_ms))

        if elapsed_ms > SLOW_THRESHOLD_MS:
            log.warning(f"[慢接口] {key} 耗时 {format_duration(elapsed_ms)}")

    # ── 用例级别 ──

    def start_test(self):
        """用例开始时调用，清空当前用例的记录"""
        with self._lock:
            self._test_records = []

    def get_test_records(self):
        """用例结束时调用，返回当前用例内所有请求记录"""
        with self._lock:
            return list(self._test_records)

    def format_test_report(self):
        """生成当前用例的耗时明细表（文本格式，用于 Allure attach）"""
        records = self.get_test_records()
        if not records:
            return ""

        total_ms = sum(r[2] for r in records)
        lines = [
            f"{'序号':<5} {'方法':<7} {'接口URL':<90} {'耗时':>10}",
            "-" * 120,
        ]
        for i, (method, url, ms) in enumerate(records, 1):
            tag = " ⚠️慢" if ms > SLOW_THRESHOLD_MS else ""
            lines.append(f"{i:<5} {method:<7} {url:<90} {format_duration(ms):>10}{tag}")

        lines.append("-" * 120)
        lines.append(f"{'合计':<5} {'':<7} {f'共 {len(records)} 个请求':<90} {format_duration(total_ms):>10}")
        return "\n".join(lines)

    # ── 全局统计 ──

    def report(self):
        with self._lock:
            data = {k: list(v) for k, v in self._global_data.items()}

        if not data:
            return "无请求数据"

        total_requests = sum(len(v) for v in data.values())
        total_time = sum(sum(v) for v in data.values())

        sep_len = 120
        lines = [
            "",
            "=" * sep_len,
            f"  接口性能统计  |  总请求: {total_requests}  |  总耗时: {format_duration(total_time)}",
            "=" * sep_len,
            f"{'接口':<90} {'次数':>5} {'P50':>10} {'P90':>10} {'P99':>10} {'Max':>10}",
            "-" * sep_len,
        ]

        for key, times in sorted(data.items(), key=lambda x: max(x[1]), reverse=True):
            n = len(times)
            p50 = statistics.median(times)
            p90 = _percentile(times, 90)
            p99 = _percentile(times, 99)
            mx = max(times)
            lines.append(
                f"{key:<90} {n:>5} {format_duration(p50):>10} {format_duration(p90):>10} {format_duration(p99):>10} {format_duration(mx):>10}"
            )

        lines.append("=" * sep_len)
        return "\n".join(lines)

    def allure_global_report(self):
        """生成全局统计并 attach 到 Allure（session 结束时调用）"""
        try:
            import allure
            text = self.report()
            if text != "无请求数据":
                allure.attach(text, "全局接口性能统计", allure.attachment_type.TEXT)
        except Exception:
            pass

    def reset(self):
        with self._lock:
            self._global_data.clear()
            self._test_records.clear()


def _percentile(data, pct):
    s = sorted(data)
    idx = min(int(len(s) * pct / 100), len(s) - 1)
    return s[idx]


perf = PerfCollector()
