from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt


PROVIDERS = {
    "deepseek": ["DEEPSEEK_API_KEY"],
    "claude": ["ANTHROPIC_API_KEY"],
    "google": ["GOOGLE_API_KEY"],
    "chatgpt": ["OPENAI_API_KEY"],
    "ollama": [],
}


def run_setup(force: bool = False) -> None:
    console = Console()
    env_path = Path(".env")

    if env_path.exists() and not force:
        console.print("[yellow].env file already exists. Use --force to overwrite.[/yellow]")
        return

    console.print("[bold]DevPy Setup Wizard[/bold]\n")

    provider = Prompt.ask(
        "Select LLM provider",
        choices=list(PROVIDERS.keys()),
        default="ollama",
    )

    lines = [f"LLM_PROVIDER={provider}"]

    for key in PROVIDERS[provider]:
        value = Prompt.ask(f"Enter {key}")
        lines.append(f"{key}={value}")

    if provider == "ollama":
        host = Prompt.ask("Ollama host", default="localhost")
        port = Prompt.ask("Ollama port", default="11434")
        model = Prompt.ask("Ollama model", default="llama3")
        lines.extend([
            f"OLLAMA_HOST={host}",
            f"OLLAMA_PORT={port}",
            f"OLLAMA_MODEL={model}",
        ])

    env_path.write_text("\n".join(lines) + "\n")
    console.print(f"\n[green]Configuration saved to {env_path}[/green]")
