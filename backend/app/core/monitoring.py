"""监控指标收集器 —— 训练指标、API 响应时间、错误率。"""

import logging
import time
from collections import defaultdict
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Prometheus 格式指标收集器（内存实现，适合单实例部署）。"""

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, list] = defaultdict(list)

    # ── Counter ───────────────────────────────────────────────────────
    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        key = self._label_key(name, labels)
        self._counters[key] += value

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        return self._counters.get(self._label_key(name, labels), 0.0)

    # ── Gauge ─────────────────────────────────────────────────────────
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        key = self._label_key(name, labels)
        self._gauges[key] = value

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        return self._gauges.get(self._label_key(name, labels), 0.0)

    # ── Histogram ─────────────────────────────────────────────────────
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        key = self._label_key(name, labels)
        self._histograms[key].append(value)
        # 保留最近 1000 个观测值
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]

    # ── 便捷方法 ──────────────────────────────────────────────────────
    def record_api_request(self, method: str, path: str, status_code: int, duration: float):
        """记录 API 请求指标。"""
        labels = {"method": method, "path": path, "status": str(status_code)}
        self.inc_counter("http_requests_total", labels=labels)
        self.observe_histogram("http_request_duration_seconds", duration, labels=labels)

        if status_code >= 500:
            self.inc_counter("http_errors_total", labels={"type": "5xx", "path": path})
        elif status_code >= 400:
            self.inc_counter("http_errors_total", labels={"type": "4xx", "path": path})

    def record_training_metric(self, model_id: str, metric_name: str, value: float):
        """记录训练指标。"""
        labels = {"model_id": model_id, "metric": metric_name}
        self.set_gauge("training_metric", value, labels=labels)

    # ── Prometheus 格式输出 ───────────────────────────────────────────
    def render_prometheus(self) -> str:
        """导出 Prometheus 文本格式指标。"""
        lines: list[str] = []

        for key, val in sorted(self._counters.items()):
            name, label_str = self._parse_key(key)
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{label_str} {val}")

        for key, val in sorted(self._gauges.items()):
            name, label_str = self._parse_key(key)
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{label_str} {val}")

        for key, vals in sorted(self._histograms.items()):
            if not vals:
                continue
            name, label_str = self._parse_key(key)
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_count{label_str} {len(vals)}")
            lines.append(f"{name}_sum{label_str} {sum(vals):.6f}")

        return "\n".join(lines) + "\n"

    # ── 内部工具 ──────────────────────────────────────────────────────
    @staticmethod
    def _label_key(name: str, labels: Optional[Dict[str, str]] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @staticmethod
    def _parse_key(key: str):
        """将 'name{k="v"}' 拆分为 (name, '{k="v"}')。"""
        if "{" in key:
            idx = key.index("{")
            return key[:idx], key[idx:]
        return key, ""


# 全局单例
metrics = MetricsCollector()
