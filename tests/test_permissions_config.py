from devpy.security.permissions_config import PermissionConfigManager


class TestPermissionConfigManager:
    def test_add_and_list(self, tmp_dir):
        pcm = PermissionConfigManager(config_file=str(tmp_dir / "perm.json"))
        pcm.add_rule("create_container", "allow")
        rules = pcm.list_rules()
        assert len(rules) == 1
        assert rules[0]["operation"] == "create_container"
        assert rules[0]["decision"] == "allow"
        pcm.close()

    def test_get_decision(self, tmp_dir):
        pcm = PermissionConfigManager(config_file=str(tmp_dir / "perm.json"))
        pcm.add_rule("delete_container", "deny")
        assert pcm.get_decision("delete_container") == "deny"
        pcm.close()

    def test_get_decision_not_found(self, tmp_dir):
        pcm = PermissionConfigManager(config_file=str(tmp_dir / "perm.json"))
        assert pcm.get_decision("unknown_op") is None
        pcm.close()

    def test_reset(self, tmp_dir):
        pcm = PermissionConfigManager(config_file=str(tmp_dir / "perm.json"))
        pcm.add_rule("op1", "allow")
        pcm.add_rule("op2", "deny")
        pcm.reset()
        assert pcm.list_rules() == []
        pcm.close()

    def test_persist_across_instances(self, tmp_dir):
        path = str(tmp_dir / "perm.json")
        pcm1 = PermissionConfigManager(config_file=path)
        pcm1.add_rule("test_op", "allow")
        pcm1.close()

        pcm2 = PermissionConfigManager(config_file=path)
        assert pcm2.get_decision("test_op") == "allow"
        pcm2.close()

    def test_multiple_rules(self, tmp_dir):
        pcm = PermissionConfigManager(config_file=str(tmp_dir / "perm.json"))
        pcm.add_rule("op_a", "allow")
        pcm.add_rule("op_b", "deny")
        pcm.add_rule("op_c", "allow")
        rules = pcm.list_rules()
        assert len(rules) == 3
        pcm.close()
