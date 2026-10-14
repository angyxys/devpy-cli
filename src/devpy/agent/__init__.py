from devpy.agent.monitoring import MonitorRegistry
from devpy.config.manager import ConfigManager
from devpy.docker.client import DockerClientFactory
from devpy.security.keys import SSHKeyManager
from devpy.security.permissions import PermissionManager


class AppContext:
    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        key_manager: SSHKeyManager | None = None,
        permission_manager: PermissionManager | None = None,
        docker_factory: DockerClientFactory | None = None,
        console=None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.key_manager = key_manager or SSHKeyManager()
        self.permission_manager = permission_manager or PermissionManager()
        self.docker_factory = docker_factory or DockerClientFactory()
        self.monitor_registry = MonitorRegistry()
        self.console = console
        self._passphrase_func = None

    def set_passphrase_func(self, func):
        self._passphrase_func = func

    def get_docker_client(self):
        return self.docker_factory.get_client(
            self.config_manager,
            self.key_manager,
            self._passphrase_func,
        )
