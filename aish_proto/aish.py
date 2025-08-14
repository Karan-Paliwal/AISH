# aish.py
import typer
from typing import List
from rich import print as rprint

from parser import find_command
from safety import is_safe
from executor import run_command
from explain import explain_command

app = typer.Typer(
    add_completion=False,
    help="AISH prototype: suggest a shell command from natural language, explain it, and (optionally) run it."
)

@app.command("suggest")
def suggest(
    nl: List[str] = typer.Argument(
        ..., metavar="NL", help="Natural language instruction, e.g. list all files sorted by size"
    )
):
    """
    Suggest and optionally run a command for the given natural-language instruction.
    """
    user_input = " ".join(nl).strip()
    if not user_input:
        rprint("[red]No input provided.[/red]")
        raise typer.Exit(code=1)

    cmd = find_command(user_input)
    if not cmd:
        rprint(f"[red]No matching command found for:[/red] {user_input!r}")
        raise typer.Exit(code=2)

    rprint(f"[green]Suggested:[/green] {cmd}")
    rprint(f"[yellow]Explanation:[/yellow] {explain_command(cmd)}")

    if not is_safe(cmd):
        rprint("[red]Blocked: Unsafe command detected.[/red]")
        raise typer.Exit(code=3)

    if typer.confirm("Run this command?", default=False):
        run_command(cmd)
    else:
        rprint("[cyan]Cancelled.[/cyan]")

@app.callback()
def main():
    """Use a subcommand like: suggest"""

if __name__ == "__main__":
    app()
