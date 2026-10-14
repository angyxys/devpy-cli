import json

import pytest

from devpy.config.manager import ConfigManager


class TestConfigManager:
    def test_defaults_when_no_file(self, tmp_dir):
        cm = ConfigManager(config_file=str(tmp_dir / "missing.json"))
        assert cm.get_mode() == "local"
        assert cm.get_ssh_config().host == ""

    def test_get_mode(self, config_file):
        cm = ConfigManager(config_file=config_file)
        assert cm.get_mode() == "local"

    def test_set_mode_local(self, config_file):
        cm = ConfigManager(config_file=config_file)
        cm.set_mode("local")
        assert cm.get_mode() == "local"

    def test_set_mode_ssh(self, config_file):
        cm = ConfigManager(config_file=config_file)
        cm.set_mode("ssh")
        assert cm.get_mode() == "ssh"

    def test_set_mode_invalid(self, config_file):
        cm = ConfigManager(config_file=config_file)
        with pytest.raises(ValueError, match="local.*ssh"):
            cm.set_mode("invalid")

    def test_ssh_config_roundtrip(self, config_file):
        cm = ConfigManager(config_file=config_file)
        cm.set_ssh_config("192.168.1.1", "admin", "my_key")
        ssh = cm.get_ssh_config()
        assert ssh.host == "192.168.1.1"
        assert ssh.user == "admin"
        assert ssh.key_name == "my_key"
        assert ssh.is_complete()

    def test_ssh_config_incomplete(self, config_file):
        cm = ConfigManager(config_file=config_file)
        ssh = cm.get_ssh_config()
        assert not ssh.is_complete()

    def test_persist_across_instances(self, config_file):
        cm1 = ConfigManager(config_file=config_file)
        cm1.set_mode("ssh")
        cm1.set_ssh_config("host1", "user1", "key1")

        cm2 = ConfigManager(config_file=config_file)
        assert cm2.get_mode() == "ssh"
        assert cm2.get_ssh_config().host == "host1"

    def test_corrupt_file_returns_defaults(self, tmp_dir):
        path = tmp_dir / "bad.json"
        path.write_text("not valid json {{{")
        cm = ConfigManager(config_file=str(path))
        assert cm.get_mode() == "local"
