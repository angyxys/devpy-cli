import getpass
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from devpy.security.permissions_config import PermissionConfigManager


class PermissionDecision:
    ALLOW_ONCE = "allow_once"
    ALLOW_COMMAND = "allow_command"
    ALLOW_SESSION = "allow_session"
    DENY = "deny"


READ_OPS = frozenset({
    "list_containers",
    "get_logs",
    "inspect_container",
    "list_images",
    "list_volumes",
    "list_networks",
    "check_resource",
})


class PermissionManager:
    def __init__(
        self,
        whitelist: set[str] | None = None,
        dry_run: bool | None = None,
        user: str | None = None,
        log_file: str | None = None,
    ):
        env_whitelist: set[str] = set()
        raw = os.getenv("DOCKER_SAFE_COMMANDS", "")
        for item in raw.split(","):
            value = item.strip()
            if value:
                env_whitelist.add(value)

        self.whitelist = (set(whitelist) | env_whitelist) if whitelist is not None else env_whitelist

        if dry_run is None:
            self.dry_run = os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes", "y"}
        else:
            self.dry_run = dry_run

        if user is None:
            env_user = os.getenv("DOCKER_CLI_USER")
            if env_user:
                self.user = env_user
            else:
                try:
                    self.user = getpass.getuser()
                except Exception:
                    self.user = "unknown"
        else:
            self.user = user

        if log_file is None:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = logs_dir / "permissions.log"
        else:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.session_approvals: dict[str, set[str]] = {"session": set(), "command": set()}
        self.config_manager = PermissionConfigManager()

    def close(self):
        self.config_manager.close()

    def needs_confirmation(self, operation: str, command_key: str | None = None) -> bool:
        if operation in self.whitelist:
            return False
        if operation in self.session_approvals["session"]:
            return False
        if command_key and command_key in self.session_approvals["command"]:
            return False
        if self.config_manager.get_decision(operation) == "allow":
            return False
        return operation not in READ_OPS

    def _log(self, operation, args, decision, dry_run, command_preview, impact, duration_ms=0):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": self.user,
            "operation": operation,
            "args": args or {},
            "decision": decision,
            "dry_run": dry_run,
            "command_preview": command_preview,
            "impact": impact,
            "duration_ms": duration_ms,
        }
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def execute(
        self,
        operation: str,
        fn,
        fn_args=None,
        fn_kwargs=None,
        command_preview: str | None = None,
        impact: str | None = None,
        command_key: str | None = None,
        prompt_func=None,
        decision_override: str | None = None,
    ):
        start = time.time()
        fn_args = fn_args or ()
        fn_kwargs = fn_kwargs or {}
        args_snapshot = {"args": list(fn_args), "kwargs": fn_kwargs}

        if self.config_manager.get_decision(operation) == "deny":
            duration = (time.time() - start) * 1000
            self._log(operation, args_snapshot, "denied_by_config", self.dry_run, command_preview, impact, duration)
            return "Operation denied by persistent configuration"

        decision = PermissionDecision.ALLOW_ONCE
        if self.needs_confirmation(operation, command_key):
            if decision_override is not None:
                decision = decision_override
            elif prompt_func is not None:
                decision = prompt_func(operation, impact, command_preview)
            else:
                decision = PermissionDecision.DENY

            if decision == PermissionDecision.DENY:
                duration = (time.time() - start) * 1000
                self._log(operation, args_snapshot, "denied", self.dry_run, command_preview, impact, duration)
                return "Operation cancelled by user"

            if decision == PermissionDecision.ALLOW_COMMAND:
                if command_key:
                    self.session_approvals["command"].add(command_key)
            elif decision == PermissionDecision.ALLOW_SESSION:
                self.session_approvals["session"].add(operation)

        if self.dry_run:
            duration = (time.time() - start) * 1000
            self._log(operation, args_snapshot, "allowed_dry_run", True, command_preview, impact, duration)
            return f"Dry-run mode: would execute {command_preview}"

        try:
            result = fn(*fn_args, **fn_kwargs)
            duration = (time.time() - start) * 1000
            self._log(operation, args_snapshot, "allowed", False, command_preview, impact, duration)
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._log(operation, args_snapshot, f"error: {e}", False, command_preview, impact, duration)
            raise
