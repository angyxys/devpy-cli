import pytest

from devpy.security.keys import SSHKeyManager


class TestSSHKeyManager:
    def test_add_and_list(self, enc_storage, ssh_key_file):
        km = SSHKeyManager(storage_file=enc_storage)
        km.add_key("test", ssh_key_file, "secret123")
        assert "test" in km.list_keys()

    def test_get_key_roundtrip(self, enc_storage, ssh_key_file):
        km = SSHKeyManager(storage_file=enc_storage)
        km.add_key("mykey", ssh_key_file, "pass")
        content = km.get_key("mykey", "pass")
        assert "RSA PRIVATE KEY" in content

    def test_get_key_wrong_passphrase(self, enc_storage, ssh_key_file):
        km = SSHKeyManager(storage_file=enc_storage)
        km.add_key("mykey", ssh_key_file, "correct")
        with pytest.raises(Exception):
            km.get_key("mykey", "wrong")

    def test_get_key_not_found(self, enc_storage):
        km = SSHKeyManager(storage_file=enc_storage)
        with pytest.raises(ValueError, match="not found"):
            km.get_key("nonexistent", "pass")

    def test_delete_key(self, enc_storage, ssh_key_file):
        km = SSHKeyManager(storage_file=enc_storage)
        km.add_key("to_delete", ssh_key_file, "pass")
        assert km.delete_key("to_delete")
        assert "to_delete" not in km.list_keys()

    def test_delete_nonexistent(self, enc_storage):
        km = SSHKeyManager(storage_file=enc_storage)
        assert not km.delete_key("nope")

    def test_multiple_keys(self, enc_storage, ssh_key_file):
        km = SSHKeyManager(storage_file=enc_storage)
        km.add_key("key1", ssh_key_file, "pass1")
        km.add_key("key2", ssh_key_file, "pass2")
        keys = km.list_keys()
        assert "key1" in keys
        assert "key2" in keys

    def test_empty_list(self, enc_storage):
        km = SSHKeyManager(storage_file=enc_storage)
        assert km.list_keys() == []

    def test_load_pkey_invalid(self):
        with pytest.raises(ValueError, match="Unsupported SSH key format"):
            SSHKeyManager.load_pkey("not a real key")
