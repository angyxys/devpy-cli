import threading
from typing import Callable


class MonitorRegistry:
    def __init__(self):
        self._monitors: dict[str, dict] = {}
        self._lock = threading.Lock()

    def start(
        self,
        container_name: str,
        threshold: float,
        check_fn: Callable[[str], float | None],
        alert_fn: Callable[[str, float, float], None],
    ) -> str:
        stop_event = threading.Event()

        def loop():
            while not stop_event.is_set():
                try:
                    mem_percent = check_fn(container_name)
                    if mem_percent is not None and mem_percent > threshold:
                        alert_fn(container_name, mem_percent, threshold)
                        self.stop(container_name)
                        return
                except Exception:
                    pass
                stop_event.wait(10)

        with self._lock:
            if container_name in self._monitors:
                self._monitors[container_name]["stop"].set()
            t = threading.Thread(target=loop, daemon=True)
            self._monitors[container_name] = {
                "thread": t,
                "stop": stop_event,
                "threshold": threshold,
            }

        t.start()
        return f"Monitoring started for '{container_name}' at {threshold}% threshold"

    def stop(self, container_name: str) -> bool:
        with self._lock:
            monitor = self._monitors.pop(container_name, None)
        if monitor:
            monitor["stop"].set()
            return True
        return False

    def list_active(self) -> dict[str, float]:
        with self._lock:
            return {name: info["threshold"] for name, info in self._monitors.items()}

    def stop_all(self):
        with self._lock:
            for info in self._monitors.values():
                info["stop"].set()
            self._monitors.clear()
