"""Command-line interface for aiready."""

import asyncio
from typing import Optional, Tuple

import click
from dotenv import load_dotenv
from rich.console import Console

from .generator import generate_llmstxt

console = Console()


@click.command()
@click.argument("source")
@click.option(
    "--output", "-o",
    default=".",
    help="Output directory for generated files",
)
@click.option(
    "--include", "-i",
    multiple=True,
    help="Include only paths matching pattern (can be used multiple times)",
)
@click.option(
    "--exclude", "-e",
    multiple=True,
    help="Exclude paths matching pattern (can be used multiple times)",
)
@click.option(
    "--max-pages", "-m",
    default=100,
    help="Maximum number of pages to process",
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="Skip AI summarization, use page titles only",
)
@click.option(
    "--api-key", "-k",
    envvar="BINERIC_API_KEY",
    help="API key for AI summarization (or set BINERIC_API_KEY env var)",
)
def main(
    source: str,
    output: str,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    max_pages: int,
    no_ai: bool,
    api_key: Optional[str],
) -> None:
    """Make your site AI ready.

    Generate llms.txt for a website or local folder.

    SOURCE can be a URL (https://example.com) or a local path (./docs)

    Examples:

        aiready https://docs.example.com

        aiready ./my-docs --output ./output

        aiready https://example.com --include "/docs/*" --max-pages 50
    """
    load_dotenv()

    console.print("""
[bold magenta]
        _                     _
   __ _(_)_ __ ___  __ _  __| |_   _
  / _` | | '__/ _ \/ _` |/ _` | | | |
 | (_| | | | |  __/ (_| | (_| | |_| |
  \__,_|_|_|  \___|\__,_|\__,_|\__, |
                               |___/
[/bold magenta]
[dim]Make your site AI ready[/dim]
""")

    include_patterns = list(include) if include else None
    exclude_patterns = list(exclude) if exclude else None

    try:
        asyncio.run(
            generate_llmstxt(
                source=source,
                output_dir=output,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                max_pages=max_pages,
                api_key=api_key,
                use_ai=not no_ai,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()


if __name__ == "__main__":
    main()
