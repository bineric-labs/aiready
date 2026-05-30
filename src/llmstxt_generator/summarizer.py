"""Generate titles and descriptions using LLM."""

import os
from typing import Optional

from anthropic import Anthropic
from rich.console import Console

console = Console()


class Summarizer:
    """Generate concise titles and descriptions for pages using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BINERIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            console.print("[yellow]No API key found. Using page titles only.[/yellow]")
            self.client = None
        else:
            base_url = os.getenv("BINERIC_API_URL", "https://api.anthropic.com")
            self.client = Anthropic(api_key=self.api_key, base_url=base_url)

    def summarize_page(self, title: str, content: str, url: str) -> dict:
        """Generate a concise title and description for a page."""
        if not self.client:
            return {
                "title": title or self._title_from_url(url),
                "description": "",
            }

        content_preview = content[:3000] if content else ""

        prompt = f"""Analyze this webpage and provide:
1. A concise title (3-5 words, descriptive)
2. A one-sentence description (max 15 words, explains what users will learn/find)

URL: {url}
Original title: {title}

Content preview:
{content_preview}

Respond in this exact format:
TITLE: <your title>
DESCRIPTION: <your description>"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            lines = text.strip().split("\n")

            result_title = title
            result_desc = ""

            for line in lines:
                if line.startswith("TITLE:"):
                    result_title = line.replace("TITLE:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    result_desc = line.replace("DESCRIPTION:", "").strip()

            return {
                "title": result_title,
                "description": result_desc,
            }

        except Exception as e:
            console.print(f"[red]Summarization error: {e}[/red]")
            return {
                "title": title or self._title_from_url(url),
                "description": "",
            }

    def summarize_site(self, pages: list[dict]) -> dict:
        """Generate a site-level title and description."""
        if not self.client or not pages:
            return {
                "title": "Documentation",
                "description": "",
            }

        page_titles = [p.get("title", "") for p in pages[:20] if p.get("title")]
        titles_text = "\n".join(f"- {t}" for t in page_titles)

        prompt = f"""Based on these page titles from a website, generate:
1. A site title (2-4 words)
2. A brief site description (one sentence, max 20 words)

Page titles:
{titles_text}

Respond in this exact format:
TITLE: <site title>
DESCRIPTION: <site description>"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            lines = text.strip().split("\n")

            result = {"title": "Documentation", "description": ""}

            for line in lines:
                if line.startswith("TITLE:"):
                    result["title"] = line.replace("TITLE:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    result["description"] = line.replace("DESCRIPTION:", "").strip()

            return result

        except Exception as e:
            console.print(f"[red]Site summarization error: {e}[/red]")
            return {"title": "Documentation", "description": ""}

    def _title_from_url(self, url: str) -> str:
        """Generate a basic title from URL path."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return parsed.netloc

        last_segment = path.split("/")[-1]
        last_segment = last_segment.replace("-", " ").replace("_", " ")
        last_segment = last_segment.rsplit(".", 1)[0]

        return last_segment.title()
