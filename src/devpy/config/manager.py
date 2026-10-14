import json
import os
from dataclasses import dataclass


@dataclass
class SSHConfig:
    host: str = ""
    user: str = ""
    key_name: str = ""

    def is_complete(self) -> bool:
        return bool(self.host and self.user and self.key_name)


class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.config_file):
            return {"mode": "local", "ssh": {"host": "", "user": "", "key_name": ""}}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"mode": "local", "ssh": {"host": "", "user": "", "key_name": ""}}

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def get_mode(self) -> str:
        return self._config.get("mode", "local")

    def set_mode(self, mode: str):
        if mode not in ("local", "ssh"):
            raise ValueError("Mode must be 'local' or 'ssh'")
        self._config["mode"] = mode
        self.save()

    def get_ssh_config(self) -> SSHConfig:
        raw = self._config.get("ssh", {})
        return SSHConfig(
            host=raw.get("host", ""),
            user=raw.get("user", ""),
            key_name=raw.get("key_name", ""),
        )

    def set_ssh_config(self, host: str, user: str, key_name: str):
        self._config["ssh"] = {"host": host, "user": user, "key_name": key_name}
        self.save()
