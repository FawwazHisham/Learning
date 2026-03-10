"""
01_foundations/03_rich_output.py
=================================
Foundation: Beautiful Terminal Output with rich

CONCEPTS COVERED:
  - Console, print with markup
  - Tables, panels, syntax highlighting
  - Progress bars (for LLM batch jobs)
  - Live displays (streaming LLM output)
  - Logging integration with rich
  - Inspecting Python objects
"""

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.markdown import Markdown
from rich.tree import Tree
from rich import inspect
from rich.logging import RichHandler
import logging

# ── 1. Console — the central object ───────────────────────────────────────────
console = Console()

# Basic printing with markup
console.print("Hello [bold magenta]World[/bold magenta]!")
console.print("[green]✓[/green] Success!")
console.print("[red]✗[/red] Error: something failed")
console.print("[yellow]⚠[/yellow] Warning: check config")

# ── 2. Panels — bordered boxes ────────────────────────────────────────────────
console.print(Panel(
    "[bold]AI Agent System[/bold]\n"
    "Powered by LangGraph + LangChain",
    title="[cyan]Welcome[/cyan]",
    border_style="green",
    expand=False,
))

# ── 3. Tables — display structured data ───────────────────────────────────────
def display_models_table():
    table = Table(title="Available AI Models", show_lines=True)

    table.add_column("Provider",  style="cyan",  no_wrap=True)
    table.add_column("Model",     style="magenta")
    table.add_column("Context",   justify="right", style="green")
    table.add_column("Best For",  style="white")

    table.add_row("Anthropic", "claude-sonnet-4-6",    "200k",  "Complex reasoning")
    table.add_row("OpenAI",    "gpt-4o",               "128k",  "Multimodal tasks")
    table.add_row("OpenAI",    "gpt-4o-mini",          "128k",  "Fast, cheap tasks")
    table.add_row("Anthropic", "claude-haiku-4-5",     "200k",  "Speed-critical paths")

    console.print(table)

display_models_table()

# ── 4. Syntax highlighting — display code snippets ────────────────────────────
def display_code(code: str, language: str = "python"):
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold]{language.upper()}[/bold]"))

sample_agent_code = '''
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list[str]
    next_step: str

def router(state: AgentState) -> str:
    return state["next_step"]
'''
display_code(sample_agent_code)

# ── 5. Progress bars — perfect for batch LLM processing ───────────────────────
def batch_process_demo():
    items = ["doc_1.txt", "doc_2.txt", "doc_3.txt", "doc_4.txt", "doc_5.txt"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding documents...", total=len(items))
        for item in items:
            time.sleep(0.3)  # simulate API call
            progress.advance(task)
            progress.print(f"  ✓ Processed {item}")

    console.print("[green bold]All documents embedded![/green bold]")

batch_process_demo()

# ── 6. Live display — simulate streaming LLM output ───────────────────────────
def simulate_streaming():
    tokens = "The answer to your question is: LangGraph is a library for building stateful, multi-actor applications with LLMs.".split()

    console.print("\n[bold cyan]Streaming response:[/bold cyan]")
    collected = ""

    with Live(console=console, refresh_per_second=20) as live:
        for token in tokens:
            collected += token + " "
            live.update(Panel(
                collected,
                title="[bold]Assistant[/bold]",
                border_style="blue",
            ))
            time.sleep(0.08)  # simulate token streaming delay

simulate_streaming()

# ── 7. Tree — visualize agent graph structure ─────────────────────────────────
def display_agent_tree():
    tree = Tree("[bold green]Agent Graph[/bold green]")

    entry = tree.add("[cyan]__start__[/cyan]")
    supervisor = entry.add("[yellow]supervisor_node[/yellow]")

    researcher = supervisor.add("[blue]researcher_agent[/blue]")
    researcher.add("search_web_tool")
    researcher.add("read_document_tool")

    writer = supervisor.add("[blue]writer_agent[/blue]")
    writer.add("draft_report_tool")
    writer.add("format_output_tool")

    supervisor.add("[red]__end__[/red]")

    console.print(tree)

display_agent_tree()

# ── 8. Markdown rendering ─────────────────────────────────────────────────────
md_content = """
# LangGraph Summary

## Key Concepts
- **StateGraph**: The main graph class
- **Nodes**: Functions that transform state
- **Edges**: Connections between nodes
- **Conditional Edges**: Routing based on state

## Quick Start
```python
graph = StateGraph(MyState)
graph.add_node("agent", agent_fn)
graph.add_edge("agent", END)
```
"""
console.print(Markdown(md_content))

# ── 9. Rich + loguru integration ──────────────────────────────────────────────
# Replace the standard Python logger with rich handler for colorized logs
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
std_logger = logging.getLogger("agent")
std_logger.info("Rich logging is active")
std_logger.warning("This is a warning")
std_logger.error("This is an error (with rich tracebacks!)")

if __name__ == "__main__":
    console.print(Panel(
        "[bold green]All rich demos complete![/bold green]",
        border_style="green"
    ))
