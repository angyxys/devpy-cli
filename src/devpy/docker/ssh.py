import paramiko
from docker.transport import SSHHTTPAdapter


class InMemorySSHAdapter(SSHHTTPAdapter):
    def __init__(self, base_url: str, pkey: paramiko.PKey, **kwargs):
        self._pkey = pkey
        super().__init__(base_url, **kwargs)

    def _create_paramiko_client(self, base_url):
        super()._create_paramiko_client(base_url)
        self.ssh_params["pkey"] = self._pkey
        self.ssh_params.pop("key_filename", None)


def get_remote_stats(host: str, user: str, pkey: paramiko.PKey) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, pkey=pkey)
        cmd = (
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | head -1; "
            "free | awk 'NR==2{printf \"%.1f %d %d\\n\", $3*100/$2, $3/1024, $2/1024}'; "
            "df -h / | awk 'NR==2{print $5, $3, $2}'"
        )
        _, stdout, _ = client.exec_command(cmd)
        lines = stdout.read().decode("utf-8").strip().splitlines()
        if len(lines) >= 3:
            cpu = lines[0].strip()
            mem_parts = lines[1].strip().split()
            disk_parts = lines[2].strip().split()
            return (
                f"CPU: {cpu}%, "
                f"Memory: {mem_parts[0]}% ({mem_parts[1]}MB/{mem_parts[2]}MB), "
                f"Disk: {disk_parts[0]} ({disk_parts[1]}/{disk_parts[2]})"
            )
        return "Unable to parse remote system stats"
    finally:
        client.close()
