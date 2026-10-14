import json
import os
import threading
import time
from datetime import datetime, timezone


class PermissionConfigManager:
    def __init__(self, config_file: str = "permissions_config.json"):
        self.config_file = config_file
        self._lock = threading.Lock()
        self._config = self._load()
        self._last_mtime = self._get_mtime()
        self._stop_event = threading.Event()
        self._start_watcher()

    def _get_mtime(self) -> float:
        try:
            return os.path.getmtime(self.config_file)
        except OSError:
            return 0

    def _load(self) -> dict:
        if not os.path.exists(self.config_file):
            return {"version": "1.0", "rules": []}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"version": "1.0", "rules": []}

    def _save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def _start_watcher(self):
        def watcher():
            while not self._stop_event.is_set():
                self._stop_event.wait(2)
                if self._stop_event.is_set():
                    break
                current = self._get_mtime()
                if current > self._last_mtime:
                    self._last_mtime = current
                    with self._lock:
                        self._config = self._load()

        t = threading.Thread(target=watcher, daemon=True)
        t.start()

    def close(self):
        self._stop_event.set()

    def add_rule(self, operation: str, decision: str, context: str = "", params: dict | None = None) -> dict:
        rule = {
            "operation": operation,
            "decision": decision,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "params": params or {},
        }
        with self._lock:
            self._config["rules"].insert(0, rule)
            self._save()
        return rule

    def get_decision(self, operation: str, params: dict | None = None) -> str | None:
        with self._lock:
            for rule in self._config.get("rules", []):
                if rule.get("operation") != operation:
                    continue
                rule_params = rule.get("params", {})
                if not rule_params:
                    return rule.get("decision")
                if params and all(params.get(k) == v for k, v in rule_params.items()):
                    return rule.get("decision")
        return None

    def list_rules(self) -> list[dict]:
        with self._lock:
            return list(self._config.get("rules", []))

    def reset(self):
        with self._lock:
            self._config = {"version": "1.0", "rules": []}
            self._save()
