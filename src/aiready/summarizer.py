"""Generate titles and descriptions using LLM."""

import os
from typing import Optional

import httpx
from rich.console import Console

console = Console()

BINERIC_API_URL = "https://api.bineric.com/v1"
BINERIC_DEFAULT_MODEL = "bineric-1"


class Summarizer:
    """Generate concise titles and descriptions for pages using LLM."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BINERIC_API_KEY")
        self.base_url = os.getenv("BINERIC_API_URL", BINERIC_API_URL)
        self.model = os.getenv("BINERIC_MODEL", BINERIC_DEFAULT_MODEL)

        if not self.api_key:
            console.print("[yellow]No API key found. Using page titles only.[/yellow]")
            console.print("[yellow]Get your API key at https://bineric.com/platform[/yellow]")
            self.client = None
        else:
            self.client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

    def _call_api(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """Make a request to the Bineric API."""
        if not self.client:
            return None

        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                console.print("[red]Invalid API key. Get your key at https://bineric.com/platform[/red]")
            else:
                console.print(f"[red]API error: {e.response.status_code}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]API error: {e}[/red]")
            return None

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

        text = self._call_api(prompt, max_tokens=150)

        if not text:
            return {
                "title": title or self._title_from_url(url),
                "description": "",
            }

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

    def summarize_site(self, pages: list) -> dict:
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

        text = self._call_api(prompt, max_tokens=100)

        if not text:
            return {"title": "Documentation", "description": ""}

        lines = text.strip().split("\n")
        result = {"title": "Documentation", "description": ""}

        for line in lines:
            if line.startswith("TITLE:"):
                result["title"] = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                result["description"] = line.replace("DESCRIPTION:", "").strip()

        return result

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
