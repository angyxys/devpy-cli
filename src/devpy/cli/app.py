import typer

from devpy.cli.commands import config_cmd, keys_cmd, permissions_cmd

app = typer.Typer(
    name="devpy",
    help="DevPy - Intelligent Docker management assistant",
    invoke_without_command=True,
)

app.add_typer(config_cmd.app, name="config")
app.add_typer(keys_cmd.app, name="keys")
app.add_typer(permissions_cmd.app, name="permissions")


@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from devpy.cli.repl import start_repl
        start_repl()


@app.command()
def setup(force: bool = typer.Option(False, "--force", help="Overwrite existing .env")):
    """Run the setup wizard to configure DevPy"""
    from devpy.cli.setup import run_setup
    run_setup(force=force)


@app.command()
def audit():
    """Run a security audit on the project"""
    from rich.console import Console
    from devpy.security.audit import run_audit

    console = Console()
    results = run_audit()

    console.print("\n[bold]File Permissions Audit:[/bold]")
    for entry in results["files"]:
        status = "[green]OK[/green]" if entry["status"] == "ok" else f"[yellow]{entry['status']}[/yellow]"
        console.print(f"  {entry['file']}: {status}")
        if entry.get("recommendation"):
            console.print(f"    {entry['recommendation']}")

    console.print("\n[bold]Dependency Audit:[/bold]")
    if results["dependencies"]:
        for warning in results["dependencies"]:
            console.print(f"  [yellow]{warning}[/yellow]")
    else:
        console.print("  [green]All dependencies pinned[/green]")


@app.command()
def version():
    """Show version information"""
    from devpy.cli.version import get_version, check_for_update
    from rich.console import Console

    console = Console()
    console.print(f"DevPy v{get_version()}")
    update_msg = check_for_update()
    if update_msg:
        console.print(f"[yellow]{update_msg}[/yellow]")


def run_cli():
    app()
