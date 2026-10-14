import base64
import json
import os
import stat
from io import StringIO

import paramiko
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SSHKeyManager:
    def __init__(self, storage_file: str = "ssh_keys.enc"):
        self.storage_file = storage_file

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

    def _load_data(self) -> dict:
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_data(self, data: dict):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(self.storage_file, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def add_key(self, name: str, key_path: str, passphrase: str):
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Key file not found: {key_path}")
        with open(key_path, "r", encoding="utf-8") as f:
            key_content = f.read()
        salt = os.urandom(16)
        derived = self._derive_key(passphrase, salt)
        fernet = Fernet(derived)
        encrypted = fernet.encrypt(key_content.encode()).decode("utf-8")
        data = self._load_data()
        data[name] = {
            "salt": base64.b64encode(salt).decode("utf-8"),
            "content": encrypted,
        }
        self._save_data(data)

    def get_key(self, name: str, passphrase: str) -> str:
        data = self._load_data()
        if name not in data:
            raise ValueError(f"Key '{name}' not found")
        record = data[name]
        salt = base64.b64decode(record["salt"])
        encrypted = record["content"].encode("utf-8")
        derived = self._derive_key(passphrase, salt)
        fernet = Fernet(derived)
        try:
            return fernet.decrypt(encrypted).decode("utf-8")
        except Exception:
            raise ValueError("Invalid passphrase or corrupted key data")

    def list_keys(self) -> list[str]:
        return list(self._load_data().keys())

    def delete_key(self, name: str) -> bool:
        data = self._load_data()
        if name in data:
            del data[name]
            self._save_data(data)
            return True
        return False

    @staticmethod
    def load_pkey(key_content: str) -> paramiko.PKey:
        key_classes = [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]
        if hasattr(paramiko, "DSSKey"):
            key_classes.append(paramiko.DSSKey)
        for key_class in key_classes:
            try:
                return key_class.from_private_key(StringIO(key_content))
            except (paramiko.SSHException, ValueError):
                continue
        raise ValueError("Unsupported SSH key format")
