from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devpy.agent import AppContext

BLOCKED_PATTERNS = [
    (r"[;&|]", "Command chaining characters (;, &, |) are not allowed"),
    (r"\$\(.*\)|`.*`", "Command substitution is not allowed"),
    (r"[><]", "I/O redirection is not allowed"),
    (r"[\n\r]", "Newlines are not allowed"),
]


def sanitize_command(command: str) -> str:
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(message)
    return command.strip()


def _cmd_preview(*parts) -> str:
    return " ".join(str(p) for p in parts)


def create_tools(ctx: AppContext) -> list:
    import docker
    import psutil
    from langchain_core.tools import tool

    from devpy.security.permissions import PermissionDecision

    def _permission_prompt(operation, impact, command_preview):
        from rich.prompt import Prompt

        ctx.console.print("\n[bold yellow]Permission Required[/bold yellow]")
        ctx.console.print(f"Operation: {operation}")
        if impact:
            ctx.console.print(f"Potential impact: {impact}")
        if command_preview:
            ctx.console.print(f"Command: {command_preview}")
        ctx.console.print("Options: (y) yes, (n) no, (yc) yes for command, (ys) yes for session")
        answer = Prompt.ask("(y/n/yc/ys)", choices=["y", "n", "yc", "ys"], default="n")
        return {
            "y": PermissionDecision.ALLOW_ONCE,
            "yc": PermissionDecision.ALLOW_COMMAND,
            "ys": PermissionDecision.ALLOW_SESSION,
        }.get(answer, PermissionDecision.DENY)

    @tool
    def check_resource() -> str:
        """Shows system CPU, memory, and disk usage of the current host"""
        mode = ctx.config_manager.get_mode()
        if mode == "ssh" and ctx.docker_factory.ssh_pkey:
            from devpy.docker.ssh import get_remote_stats

            ssh_config = ctx.config_manager.get_ssh_config()
            try:
                return get_remote_stats(ssh_config.host, ssh_config.user, ctx.docker_factory.ssh_pkey)
            except Exception as e:
                return f"Error getting remote stats: {e}"
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_usage = psutil.disk_usage("/")
        return f"CPU: {cpu}%, Memory: {memory.percent}%, Disk: {disk_usage.percent}%"

    @tool
    def get_docker_logs(container_name: str, tail: int = 50) -> str:
        """Gets the last logs of a Docker container"""
        try:
            client = ctx.get_docker_client()
            container = client.containers.get(container_name)
            logs = container.logs(tail=tail).decode("utf-8")
            return f"Logs for '{container_name}':\n{logs[-2000:]}"
        except docker.errors.NotFound:
            return f"Error: Container '{container_name}' not found"
        except Exception as e:
            return f"Error: {e}"

    @tool
    def list_containers() -> str:
        """Lists active Docker containers with their status"""
        try:
            client = ctx.get_docker_client()
            containers = client.containers.list()
            if not containers:
                return "No active containers"
            return "\n".join(f"{c.name} ({c.status})" for c in containers)
        except Exception as e:
            return f"Error listing containers: {e}"

    @tool
    def inspect_container(container_name: str) -> str:
        """Inspects a Docker container and returns its attributes"""
        try:
            client = ctx.get_docker_client()
            container = client.containers.get(container_name)
            return str(container.attrs)
        except docker.errors.NotFound:
            return f"Error: Container '{container_name}' not found"
        except Exception as e:
            return f"Error: {e}"

    @tool
    def restart_docker_container(container_name: str) -> str:
        """Restarts a specified Docker container"""
        preview = _cmd_preview("docker", "restart", container_name)

        def action():
            client = ctx.get_docker_client()
            client.containers.get(container_name).restart()
            return f"Container '{container_name}' restarted"

        return ctx.permission_manager.execute(
            operation="restart_container",
            fn=action,
            command_preview=preview,
            impact="Restarts the specified container",
            command_key=f"restart:{container_name}",
            prompt_func=_permission_prompt,
        )

    @tool
    def download_image(image_name: str) -> str:
        """Downloads a Docker image from a registry"""
        preview = _cmd_preview("docker", "pull", image_name)

        def action():
            ctx.get_docker_client().images.pull(image_name)
            return f"Image '{image_name}' downloaded"

        return ctx.permission_manager.execute(
            operation="download_image",
            fn=action,
            command_preview=preview,
            impact="Downloads a Docker image",
            command_key=f"download:{image_name}",
            prompt_func=_permission_prompt,
        )

    @tool
    def create_container(container_image: str, container_name: str) -> str:
        """Creates and starts a new Docker container with given image and name"""
        client = ctx.get_docker_client()
        existing_tags = [tag for img in client.images.list() for tag in (img.tags or [])]
        if container_image not in existing_tags:
            result = download_image.invoke({"image_name": container_image})
            if isinstance(result, str) and "Error" in result:
                return result

        preview = _cmd_preview("docker", "run", "-d", "--name", container_name, container_image)

        def action():
            c = ctx.get_docker_client()
            container = c.containers.create(container_image, name=container_name)
            container.start()
            return f"Container '{container_name}' created and started"

        return ctx.permission_manager.execute(
            operation="create_container",
            fn=action,
            command_preview=preview,
            impact="Creates and starts a new container",
            command_key=f"create:{container_image}:{container_name}",
            prompt_func=_permission_prompt,
        )

    @tool
    def delete_container(container_name: str) -> str:
        """Stops and removes the specified Docker container"""
        preview = _cmd_preview("docker", "rm", "-f", container_name)

        def action():
            client = ctx.get_docker_client()
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
            return f"Container '{container_name}' deleted"

        return ctx.permission_manager.execute(
            operation="delete_container",
            fn=action,
            command_preview=preview,
            impact="Stops and removes the specified container",
            command_key=f"delete:{container_name}",
            prompt_func=_permission_prompt,
        )

    @tool
    def stop_container(container_name: str) -> str:
        """Stops the specified Docker container"""
        preview = _cmd_preview("docker", "stop", container_name)

        def action():
            ctx.get_docker_client().containers.get(container_name).stop()
            return f"Container '{container_name}' stopped"

        return ctx.permission_manager.execute(
            operation="stop_container",
            fn=action,
            command_preview=preview,
            impact="Stops the specified container",
            command_key=f"stop:{container_name}",
            prompt_func=_permission_prompt,
        )

    @tool
    def start_monitoring(container_name: str, threshold_percent: float) -> str:
        """Starts memory monitoring for a container and alerts if threshold is exceeded"""
        preview = _cmd_preview("monitor", "memory", container_name, f"threshold={threshold_percent}")

        def check_fn(name):
            client = ctx.get_docker_client()
            stats = client.containers.get(name).stats(stream=False)
            usage = stats["memory_stats"]["usage"]
            limit = stats["memory_stats"]["limit"]
            return (usage / limit) * 100

        def alert_fn(name, current, threshold):
            ctx.console.print(
                f"\n[bold red]Alert: Memory usage of '{name}' at {current:.1f}% "
                f"(threshold: {threshold}%)[/bold red]"
            )

        def action():
            return ctx.monitor_registry.start(container_name, threshold_percent, check_fn, alert_fn)

        return ctx.permission_manager.execute(
            operation="start_monitoring",
            fn=action,
            command_preview=preview,
            impact="Starts background memory monitoring",
            command_key=f"monitor:{container_name}:{threshold_percent}",
            prompt_func=_permission_prompt,
        )

    @tool
    def stop_monitoring(container_name: str) -> str:
        """Stops memory monitoring for a container"""
        if ctx.monitor_registry.stop(container_name):
            return f"Monitoring stopped for '{container_name}'"
        return f"No active monitor found for '{container_name}'"

    @tool
    def list_monitors() -> str:
        """Lists all active memory monitors"""
        active = ctx.monitor_registry.list_active()
        if not active:
            return "No active monitors"
        return "\n".join(f"{name}: threshold {threshold}%" for name, threshold in active.items())

    @tool
    def exec_command(container_name: str, command: str) -> str:
        """Executes a shell command inside a Docker container"""
        try:
            safe_command = sanitize_command(command)
        except ValueError as e:
            return f"Security error: {e}"

        preview = _cmd_preview("docker", "exec", container_name, safe_command)

        def action():
            client = ctx.get_docker_client()
            result = client.containers.get(container_name).exec_run(safe_command)
            return result.output.decode("utf-8").strip()

        return ctx.permission_manager.execute(
            operation="exec_command",
            fn=action,
            command_preview=preview,
            impact="Executes a command inside the container",
            command_key=f"exec:{container_name}:{safe_command}",
            prompt_func=_permission_prompt,
        )

    @tool
    def delete_image(image_name: str) -> str:
        """Deletes a Docker image if it exists"""
        client = ctx.get_docker_client()
        existing_tags = [tag for img in client.images.list() for tag in (img.tags or [])]
        if image_name not in existing_tags:
            return f"Image '{image_name}' not found"

        preview = _cmd_preview("docker", "rmi", image_name)

        def action():
            ctx.get_docker_client().images.remove(image_name)
            return f"Image '{image_name}' deleted"

        return ctx.permission_manager.execute(
            operation="delete_image",
            fn=action,
            command_preview=preview,
            impact="Deletes the specified Docker image",
            command_key=f"delete_image:{image_name}",
            prompt_func=_permission_prompt,
        )

    return [
        check_resource,
        get_docker_logs,
        list_containers,
        inspect_container,
        restart_docker_container,
        download_image,
        create_container,
        delete_container,
        stop_container,
        start_monitoring,
        stop_monitoring,
        list_monitors,
        exec_command,
        delete_image,
    ]
