"""Main generator that orchestrates the llms.txt creation."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .crawler import Crawler
from .extractor import ContentExtractor
from .summarizer import Summarizer

console = Console()


class LLMSTxtGenerator:
    """Generate llms.txt files from websites or local folders."""

    def __init__(
        self,
        source: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_pages: int = 100,
        api_key: Optional[str] = None,
        use_ai: bool = True,
    ):
        self.source = source
        self.crawler = Crawler(
            source=source,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_pages=max_pages,
        )
        self.extractor = ContentExtractor()
        self.summarizer = Summarizer(api_key=api_key) if use_ai else None
        self.use_ai = use_ai

    async def generate(self) -> tuple[str, str]:
        """Generate llms.txt and llms-full.txt content."""
        console.print(f"\n[bold]Generating llms.txt for:[/bold] {self.source}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering pages...", total=None)
            pages = await self.crawler.crawl()

            if not pages:
                console.print("[red]No pages found![/red]")
                return "", ""

            progress.update(task, description="Extracting content...")
            processed_pages = []

            for page in pages:
                extracted = self.extractor.extract(page["content"], page["source"])
                page["title"] = extracted["title"]
                page["extracted_content"] = extracted["content"]
                processed_pages.append(page)

            if self.use_ai and self.summarizer:
                progress.update(task, description="Generating summaries with AI...")

                site_info = self.summarizer.summarize_site(processed_pages)

                for page in processed_pages:
                    summary = self.summarizer.summarize_page(
                        title=page["title"],
                        content=page["extracted_content"],
                        url=page["url"],
                    )
                    page["ai_title"] = summary["title"]
                    page["ai_description"] = summary["description"]
            else:
                site_info = {"title": self._get_site_name(), "description": ""}

            progress.update(task, description="Writing output...")

        llms_txt = self._format_llms_txt(site_info, processed_pages)
        llms_full_txt = self._format_llms_full_txt(site_info, processed_pages)

        return llms_txt, llms_full_txt

    def _get_site_name(self) -> str:
        """Get a basic site name from source."""
        if self.crawler.is_local:
            return Path(self.source).name

        parsed = urlparse(self.source)
        return parsed.netloc

    def _format_llms_txt(self, site_info: dict, pages: list[dict]) -> str:
        """Format the llms.txt output."""
        lines = []

        lines.append(f"# {site_info['title']}")
        if site_info.get("description"):
            lines.append(f"\n> {site_info['description']}")
        lines.append("")

        grouped = self._group_pages_by_section(pages)

        for section, section_pages in grouped.items():
            if section:
                lines.append(f"## {section}")
                lines.append("")

            for page in section_pages:
                title = page.get("ai_title") or page.get("title") or "Untitled"
                url = page["url"]
                desc = page.get("ai_description", "")

                if desc:
                    lines.append(f"- [{title}]({url}): {desc}")
                else:
                    lines.append(f"- [{title}]({url})")

            lines.append("")

        return "\n".join(lines)

    def _format_llms_full_txt(self, site_info: dict, pages: list[dict]) -> str:
        """Format the llms-full.txt output with full content."""
        lines = []

        lines.append(f"# {site_info['title']}")
        if site_info.get("description"):
            lines.append(f"\n> {site_info['description']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for i, page in enumerate(pages):
            title = page.get("ai_title") or page.get("title") or "Untitled"
            content = page.get("extracted_content", "")

            lines.append(f"## {title}")
            lines.append(f"\nSource: {page['url']}\n")

            if content:
                if len(content) > 10000:
                    content = content[:10000] + "\n\n[Content truncated...]"
                lines.append(content)

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _group_pages_by_section(self, pages: list[dict]) -> Dict[str, List[dict]]:
        """Group pages by their URL path section."""
        groups: Dict[str, List[dict]] = {"": []}

        for page in pages:
            if self.crawler.is_local:
                path = page.get("path", "")
                parts = path.split("/")
                section = parts[0] if len(parts) > 1 else ""
            else:
                parsed = urlparse(page["url"])
                parts = parsed.path.strip("/").split("/")
                section = parts[0].replace("-", " ").title() if len(parts) > 1 else ""

            if section not in groups:
                groups[section] = []
            groups[section].append(page)

        if "" in groups and not groups[""]:
            del groups[""]

        return groups


async def generate_llmstxt(
    source: str,
    output_dir: str = ".",
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_pages: int = 100,
    api_key: Optional[str] = None,
    use_ai: bool = True,
) -> None:
    """Main entry point to generate llms.txt files."""
    generator = LLMSTxtGenerator(
        source=source,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        max_pages=max_pages,
        api_key=api_key,
        use_ai=use_ai,
    )

    llms_txt, llms_full_txt = await generator.generate()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    llms_file = output_path / "llms.txt"
    llms_file.write_text(llms_txt, encoding="utf-8")
    console.print(f"[green]Created:[/green] {llms_file}")

    llms_full_file = output_path / "llms-full.txt"
    llms_full_file.write_text(llms_full_txt, encoding="utf-8")
    console.print(f"[green]Created:[/green] {llms_full_file}")

    console.print("\n[bold green]Done![/bold green]")
