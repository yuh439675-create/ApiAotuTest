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
            log.warning(f"[慢接口] {key} 耗时 {elapsed_ms:.0f}ms")

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
            f"{'序号':<5} {'方法':<7} {'接口URL':<55} {'耗时':>10}",
            "-" * 80,
        ]
        for i, (method, url, ms) in enumerate(records, 1):
            display_url = url if len(url) <= 55 else url[:52] + "..."
            tag = " ⚠️慢" if ms > SLOW_THRESHOLD_MS else ""
            lines.append(f"{i:<5} {method:<7} {display_url:<55} {ms:>8.0f}ms{tag}")

        lines.append("-" * 80)
        lines.append(f"{'合计':<5} {'':<7} {f'共 {len(records)} 个请求':<55} {total_ms:>8.0f}ms")
        return "\n".join(lines)

    # ── 全局统计 ──

    def report(self):
        with self._lock:
            data = {k: list(v) for k, v in self._global_data.items()}

        if not data:
            return "无请求数据"

        total_requests = sum(len(v) for v in data.values())
        total_time = sum(sum(v) for v in data.values())

        lines = [
            "",
            "=" * 95,
            f"  接口性能统计  |  总请求: {total_requests}  |  总耗时: {total_time:.0f}ms",
            "=" * 95,
            f"{'接口':<50} {'次数':>5} {'P50':>8} {'P90':>8} {'P99':>8} {'Max':>8}",
            "-" * 95,
        ]

        for key, times in sorted(data.items(), key=lambda x: max(x[1]), reverse=True):
            n = len(times)
            p50 = statistics.median(times)
            p90 = _percentile(times, 90)
            p99 = _percentile(times, 99)
            mx = max(times)
            dk = key if len(key) <= 50 else key[:47] + "..."
            lines.append(
                f"{dk:<50} {n:>5} {p50:>7.0f}ms {p90:>7.0f}ms {p99:>7.0f}ms {mx:>7.0f}ms"
            )

        lines.append("=" * 95)
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
