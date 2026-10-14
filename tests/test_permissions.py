from devpy.security.permissions import PermissionManager, READ_OPS


class TestPermissionManager:
    def test_read_ops_no_confirmation(self, tmp_dir):
        pm = PermissionManager()
        for op in READ_OPS:
            assert not pm.needs_confirmation(op)
        pm.close()

    def test_write_ops_need_confirmation(self, tmp_dir):
        pm = PermissionManager()
        assert pm.needs_confirmation("create_container")
        assert pm.needs_confirmation("delete_container")
        assert pm.needs_confirmation("restart_container")
        pm.close()

    def test_whitelisted_ops_skip_confirmation(self, tmp_dir):
        pm = PermissionManager(whitelist={"create_container", "delete_container"})
        assert not pm.needs_confirmation("create_container")
        assert not pm.needs_confirmation("delete_container")
        pm.close()

    def test_session_approval(self, tmp_dir):
        pm = PermissionManager()
        pm.session_approvals["session"].add("stop_container")
        assert not pm.needs_confirmation("stop_container")
        pm.close()

    def test_command_approval(self, tmp_dir):
        pm = PermissionManager()
        pm.session_approvals["command"].add("restart:web")
        assert not pm.needs_confirmation("restart_container", command_key="restart:web")
        pm.close()

    def test_execute_read_op_no_prompt(self, tmp_dir):
        pm = PermissionManager()
        result = pm.execute(
            operation="list_containers",
            fn=lambda: "container_list",
            prompt_func=lambda *a: None,
        )
        assert result == "container_list"
        pm.close()

    def test_execute_dry_run(self, tmp_dir):
        pm = PermissionManager(dry_run=True)
        result = pm.execute(
            operation="delete_container",
            fn=lambda: "deleted",
            command_preview="docker rm test",
            prompt_func=lambda *a: None,
        )
        assert "Dry-run" in result
        assert "docker rm test" in result
        pm.close()

    def test_execute_denied(self, tmp_dir):
        pm = PermissionManager()

        def deny_prompt(*args):
            from devpy.security.permissions import PermissionDecision
            return PermissionDecision.DENY

        result = pm.execute(
            operation="delete_container",
            fn=lambda: "deleted",
            prompt_func=deny_prompt,
        )
        assert "cancelled" in result.lower()
        pm.close()

    def test_execute_allow_once(self, tmp_dir):
        pm = PermissionManager()

        def allow_prompt(*args):
            from devpy.security.permissions import PermissionDecision
            return PermissionDecision.ALLOW_ONCE

        result = pm.execute(
            operation="restart_container",
            fn=lambda: "restarted",
            prompt_func=allow_prompt,
        )
        assert result == "restarted"
        assert pm.needs_confirmation("restart_container")
        pm.close()

    def test_execute_allow_session(self, tmp_dir):
        pm = PermissionManager()

        def session_prompt(*args):
            from devpy.security.permissions import PermissionDecision
            return PermissionDecision.ALLOW_SESSION

        pm.execute(
            operation="restart_container",
            fn=lambda: "restarted",
            prompt_func=session_prompt,
        )
        assert not pm.needs_confirmation("restart_container")
        pm.close()
