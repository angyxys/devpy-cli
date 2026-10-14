import typer
from rich.console import Console

from devpy.config.manager import ConfigManager

app = typer.Typer(help="Configuration management")
console = Console()


@app.command()
def mode(value: str = typer.Argument(None, help="Set mode to 'local' or 'ssh'")):
    cm = ConfigManager()
    if value is None:
        console.print(f"Current mode: {cm.get_mode()}")
        return
    try:
        cm.set_mode(value)
        console.print(f"Mode set to: {value}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def ssh(
    host: str = typer.Option(None, help="SSH host"),
    user: str = typer.Option(None, help="SSH user"),
    key_name: str = typer.Option(None, "--key", help="SSH key name"),
):
    cm = ConfigManager()
    current = cm.get_ssh_config()

    if not any([host, user, key_name]):
        console.print(f"Host: {current.host or 'not set'}")
        console.print(f"User: {current.user or 'not set'}")
        console.print(f"Key:  {current.key_name or 'not set'}")
        return

    cm.set_ssh_config(
        host=host or current.host,
        user=user or current.user,
        key_name=key_name or current.key_name,
    )
    console.print("[green]SSH configuration updated[/green]")


@app.command()
def show():
    cm = ConfigManager()
    console.print(f"Mode: {cm.get_mode()}")
    ssh_config = cm.get_ssh_config()
    console.print(f"SSH Host: {ssh_config.host or 'not set'}")
    console.print(f"SSH User: {ssh_config.user or 'not set'}")
    console.print(f"SSH Key: {ssh_config.key_name or 'not set'}")
