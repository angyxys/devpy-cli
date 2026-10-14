import typer
from rich.console import Console
from rich.prompt import Prompt

from devpy.security.keys import SSHKeyManager

app = typer.Typer(help="SSH key management")
console = Console()


@app.command("list")
def list_keys():
    km = SSHKeyManager()
    keys = km.list_keys()
    if not keys:
        console.print("No stored SSH keys")
        return
    for name in keys:
        console.print(f"  - {name}")


@app.command()
def add(name: str, key_path: str):
    passphrase = Prompt.ask("Enter passphrase for encryption", password=True)
    km = SSHKeyManager()
    try:
        km.add_key(name, key_path, passphrase)
        console.print(f"[green]Key '{name}' stored[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def delete(name: str):
    km = SSHKeyManager()
    if km.delete_key(name):
        console.print(f"[green]Key '{name}' deleted[/green]")
    else:
        console.print(f"[yellow]Key '{name}' not found[/yellow]")


@app.command()
def scan():
    from pathlib import Path

    ssh_dir = Path.home() / ".ssh"
    if not ssh_dir.exists():
        console.print("No ~/.ssh directory found")
        return

    key_files = [f for f in ssh_dir.iterdir() if f.is_file() and not f.suffix and f.name != "known_hosts" and f.name != "config" and f.name != "authorized_keys"]
    if not key_files:
        console.print("No SSH keys found in ~/.ssh")
        return

    console.print("Found SSH keys:")
    for f in key_files:
        console.print(f"  - {f.name} ({f})")
