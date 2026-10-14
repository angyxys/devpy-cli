import typer
from rich.console import Console

from devpy.security.permissions_config import PermissionConfigManager

app = typer.Typer(help="Permission rules management")
console = Console()


@app.command("list")
def list_rules():
    pcm = PermissionConfigManager()
    rules = pcm.list_rules()
    pcm.close()
    if not rules:
        console.print("No permission rules configured")
        return
    for rule in rules:
        console.print(f"  {rule['operation']}: {rule['decision']} ({rule.get('context', '')})")


@app.command()
def add(operation: str, decision: str = typer.Argument(..., help="allow or deny")):
    pcm = PermissionConfigManager()
    rule = pcm.add_rule(operation, decision)
    pcm.close()
    console.print(f"[green]Rule added: {rule['operation']} -> {rule['decision']}[/green]")


@app.command()
def reset():
    pcm = PermissionConfigManager()
    pcm.reset()
    pcm.close()
    console.print("[green]All permission rules cleared[/green]")
