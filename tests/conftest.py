import json
import os
import tempfile

import pytest


@pytest.fixture
def tmp_dir(tmp_path):
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


@pytest.fixture
def config_file(tmp_dir):
    path = tmp_dir / "config.json"
    path.write_text(json.dumps({"mode": "local", "ssh": {}}))
    return str(path)


@pytest.fixture
def empty_config_file(tmp_dir):
    path = tmp_dir / "config.json"
    return str(path)


@pytest.fixture
def ssh_key_file(tmp_dir):
    path = tmp_dir / "test_key"
    path.write_text("-----BEGIN RSA PRIVATE KEY-----\nfake-key-content\n-----END RSA PRIVATE KEY-----\n")
    return str(path)


@pytest.fixture
def enc_storage(tmp_dir):
    return str(tmp_dir / "ssh_keys.enc")
