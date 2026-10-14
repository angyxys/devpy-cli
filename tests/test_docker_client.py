from unittest.mock import patch, MagicMock

import pytest

from devpy.docker.client import DockerClientFactory
from devpy.config.manager import ConfigManager


class TestDockerClientFactory:
    def test_local_mode(self, config_file):
        factory = DockerClientFactory()
        cm = ConfigManager(config_file=config_file)
        cm.set_mode("local")

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            client = factory.get_client(cm, MagicMock())
            assert client is mock_client
            mock_docker.assert_called_once()

    def test_caches_client(self, config_file):
        factory = DockerClientFactory()
        cm = ConfigManager(config_file=config_file)

        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = MagicMock()
            c1 = factory.get_client(cm, MagicMock())
            c2 = factory.get_client(cm, MagicMock())
            assert c1 is c2
            assert mock_docker.call_count == 1

    def test_reset(self, config_file):
        factory = DockerClientFactory()
        cm = ConfigManager(config_file=config_file)

        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = MagicMock()
            factory.get_client(cm, MagicMock())
            factory.reset()
            assert factory._client is None
            assert factory.ssh_pkey is None

    def test_ssh_mode_incomplete_config(self, config_file):
        factory = DockerClientFactory()
        cm = ConfigManager(config_file=config_file)
        cm.set_mode("ssh")

        with pytest.raises(ValueError, match="incomplete"):
            factory.get_client(cm, MagicMock())

    def test_ssh_mode_no_passphrase(self, config_file):
        factory = DockerClientFactory()
        cm = ConfigManager(config_file=config_file)
        cm.set_mode("ssh")
        cm.set_ssh_config("host", "user", "key1")

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="passphrase"):
                factory.get_client(cm, MagicMock())
