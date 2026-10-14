import os

import docker
import paramiko

from devpy.config.manager import ConfigManager
from devpy.docker.ssh import InMemorySSHAdapter
from devpy.security.keys import SSHKeyManager


class DockerClientFactory:
    def __init__(self):
        self._client: docker.DockerClient | None = None
        self._ssh_pkey: paramiko.PKey | None = None

    @property
    def ssh_pkey(self) -> paramiko.PKey | None:
        return self._ssh_pkey

    def get_client(
        self,
        config_manager: ConfigManager,
        key_manager: SSHKeyManager,
        passphrase_func=None,
    ) -> docker.DockerClient:
        if self._client:
            return self._client

        mode = config_manager.get_mode()
        if mode == "local":
            self._client = docker.from_env()
            return self._client

        ssh_config = config_manager.get_ssh_config()
        if not ssh_config.is_complete():
            raise ValueError("SSH configuration incomplete. Run 'config ssh' first.")

        passphrase = os.getenv("DOCKER_SSH_PASSPHRASE")
        if not passphrase and passphrase_func:
            passphrase = passphrase_func(ssh_config.key_name)
        if not passphrase:
            raise ValueError("SSH key passphrase required")

        key_content = key_manager.get_key(ssh_config.key_name, passphrase)
        self._ssh_pkey = SSHKeyManager.load_pkey(key_content)

        ssh_url = f"ssh://{ssh_config.user}@{ssh_config.host}"
        ssh_adapter = InMemorySSHAdapter(ssh_url, pkey=self._ssh_pkey)

        api_client = docker.APIClient(base_url="http://localhost", version="auto")
        api_client.mount("http+docker://ssh", ssh_adapter)
        api_client.base_url = "http+docker://ssh"

        client = docker.DockerClient(version="auto")
        client.api = api_client
        self._client = client
        return self._client

    def reset(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._ssh_pkey = None
