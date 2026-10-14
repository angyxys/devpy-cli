from rich.console import Console
from rich.prompt import Prompt

from devpy.agent import AppContext
from devpy.agent.executor import AgentExecutor
from devpy.cli.version import check_for_update, get_version
from devpy.providers import create_llm


def _handle_config(args: list[str], ctx: AppContext, console: Console):
    if not args:
        console.print(f"Mode: {ctx.config_manager.get_mode()}")
        ssh = ctx.config_manager.get_ssh_config()
        console.print(f"SSH: {ssh.host or 'not set'} ({ssh.user or 'not set'})")
        return

    sub = args[0]
    if sub == "mode" and len(args) > 1:
        try:
            ctx.config_manager.set_mode(args[1])
            console.print(f"Mode set to: {args[1]}")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
    elif sub == "ssh" and len(args) >= 4:
        ctx.config_manager.set_ssh_config(args[1], args[2], args[3])
        console.print("[green]SSH configuration updated[/green]")
    else:
        console.print("Usage: /config mode <local|ssh> | /config ssh <host> <user> <key>")


def _handle_keys(args: list[str], ctx: AppContext, console: Console):
    if not args:
        keys = ctx.key_manager.list_keys()
        if not keys:
            console.print("No stored keys")
        else:
            for k in keys:
                console.print(f"  - {k}")
        return

    sub = args[0]
    if sub == "add" and len(args) >= 3:
        passphrase = Prompt.ask("Passphrase", password=True)
        ctx.key_manager.add_key(args[1], args[2], passphrase)
        console.print(f"[green]Key '{args[1]}' stored[/green]")
    elif sub == "delete" and len(args) >= 2:
        if ctx.key_manager.delete_key(args[1]):
            console.print(f"Key '{args[1]}' deleted")
        else:
            console.print(f"Key '{args[1]}' not found")
    else:
        console.print("Usage: /keys | /keys add <name> <path> | /keys delete <name>")


def _handle_permissions(args: list[str], ctx: AppContext, console: Console):
    if not args:
        rules = ctx.permission_manager.config_manager.list_rules()
        if not rules:
            console.print("No permission rules")
        else:
            for r in rules:
                console.print(f"  {r['operation']}: {r['decision']}")
        return

    if args[0] == "reset":
        ctx.permission_manager.config_manager.reset()
        console.print("[green]Permission rules cleared[/green]")


def _handle_monitors(args: list[str], ctx: AppContext, console: Console):
    if not args:
        active = ctx.monitor_registry.list_active()
        if not active:
            console.print("No active monitors")
        else:
            for name, threshold in active.items():
                console.print(f"  {name}: {threshold}%")
        return

    if args[0] == "stop" and len(args) >= 2:
        if ctx.monitor_registry.stop(args[1]):
            console.print(f"Monitor stopped: {args[1]}")
        else:
            console.print(f"No monitor found: {args[1]}")
    elif args[0] == "stopall":
        ctx.monitor_registry.stop_all()
        console.print("All monitors stopped")


BUILTIN_COMMANDS = {
    "/config": _handle_config,
    "/keys": _handle_keys,
    "/permissions": _handle_permissions,
    "/monitors": _handle_monitors,
}


def start_repl():
    console = Console()
    console.print(f"[bold green]DevPy v{get_version()}[/bold green]")

    update_msg = check_for_update()
    if update_msg:
        console.print(f"[yellow]{update_msg}[/yellow]")

    console.print("Type your commands or /help for available commands.\n")

    ctx = AppContext(console=console)
    ctx.set_passphrase_func(lambda key_name: Prompt.ask(f"Passphrase for '{key_name}'", password=True))

    try:
        llm = create_llm()
    except Exception as e:
        console.print(f"[red]Failed to initialize LLM: {e}[/red]")
        console.print("Run 'devpy setup' to configure your LLM provider.")
        return

    executor = AgentExecutor(ctx, llm)

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]devpy[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input.strip():
            continue

        stripped = user_input.strip()

        if stripped in ("/exit", "/quit"):
            break

        if stripped == "/help":
            console.print("Available commands:")
            console.print("  /config           - Show/set configuration")
            console.print("  /keys             - Manage SSH keys")
            console.print("  /permissions      - Manage permission rules")
            console.print("  /monitors         - View/stop monitors")
            console.print("  /exit, /quit      - Exit DevPy")
            console.print("  Anything else     - Send to AI agent")
            continue

        cmd_parts = stripped.split()
        cmd_name = cmd_parts[0]
        if cmd_name in BUILTIN_COMMANDS:
            BUILTIN_COMMANDS[cmd_name](cmd_parts[1:], ctx, console)
            continue

        try:
            response = executor.run(stripped)
            console.print(f"\n[bold]DevPy:[/bold] {response}\n")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    ctx.monitor_registry.stop_all()
    ctx.permission_manager.close()
    console.print("\n[bold]Goodbye![/bold]")
