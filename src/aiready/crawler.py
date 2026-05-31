"""Crawl websites and discover pages."""

import asyncio
import fnmatch
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()


class Crawler:
    """Discover pages from a website or local folder."""

    def __init__(
        self,
        source: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_pages: int = 100,
    ):
        self.source = source
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.max_pages = max_pages
        self.is_local = not source.startswith(("http://", "https://"))

    def _matches_patterns(self, path: str) -> bool:
        """Check if path matches include patterns and doesn't match exclude patterns."""
        included = any(fnmatch.fnmatch(path, p) for p in self.include_patterns)
        excluded = any(fnmatch.fnmatch(path, p) for p in self.exclude_patterns)
        return included and not excluded

    async def crawl(self) -> list[dict]:
        """Discover and return all pages."""
        if self.is_local:
            return self._crawl_local()
        return await self._crawl_web()

    def _crawl_local(self) -> list[dict]:
        """Crawl a local folder for markdown/html files."""
        pages = []
        root = Path(self.source)

        if not root.exists():
            raise ValueError(f"Path does not exist: {self.source}")

        extensions = {".md", ".mdx", ".html", ".htm", ".txt", ".rst"}

        for file_path in root.rglob("*"):
            if file_path.suffix.lower() not in extensions:
                continue

            rel_path = str(file_path.relative_to(root))
            if not self._matches_patterns(rel_path):
                continue

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            pages.append({
                "url": str(file_path),
                "path": rel_path,
                "content": content,
                "source": "local",
            })

            if len(pages) >= self.max_pages:
                break

        console.print(f"[green]Found {len(pages)} local files[/green]")
        return pages

    async def _crawl_web(self) -> list[dict]:
        """Crawl a website starting from sitemap or by following links."""
        pages = []
        visited = set()
        base_url = self.source.rstrip("/")
        parsed_base = urlparse(base_url)

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "llmstxt-generator/0.1.0"},
        ) as client:
            sitemap_urls = await self._get_sitemap_urls(client, base_url)

            if sitemap_urls:
                console.print(f"[green]Found {len(sitemap_urls)} URLs in sitemap[/green]")
                urls_to_crawl = sitemap_urls
            else:
                console.print("[yellow]No sitemap found, following links[/yellow]")
                urls_to_crawl = await self._discover_links(client, base_url, parsed_base)

            for url in urls_to_crawl:
                if len(pages) >= self.max_pages:
                    break

                if url in visited:
                    continue

                parsed = urlparse(url)
                if not self._matches_patterns(parsed.path):
                    continue

                visited.add(url)

                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "text/html" in content_type:
                            pages.append({
                                "url": url,
                                "path": parsed.path,
                                "content": response.text,
                                "source": "web",
                            })
                            console.print(f"[dim]Crawled: {parsed.path}[/dim]")
                except Exception as e:
                    console.print(f"[red]Error crawling {url}: {e}[/red]")

        console.print(f"[green]Crawled {len(pages)} pages[/green]")
        return pages

    async def _get_sitemap_urls(self, client: httpx.AsyncClient, base_url: str) -> list[str]:
        """Try to get URLs from sitemap.xml."""
        sitemap_locations = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap/sitemap.xml",
        ]

        for sitemap_url in sitemap_locations:
            try:
                response = await client.get(sitemap_url)
                if response.status_code == 200:
                    return self._parse_sitemap(response.text, base_url)
            except Exception:
                continue

        return []

    def _parse_sitemap(self, xml_content: str, base_url: str) -> list[str]:
        """Parse sitemap XML and extract URLs."""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            for loc in root.findall(".//sm:loc", ns):
                if loc.text:
                    urls.append(loc.text)

            if not urls:
                for loc in root.findall(".//loc"):
                    if loc.text:
                        urls.append(loc.text)

        except ET.ParseError:
            pass

        return urls

    async def _discover_links(
        self, client: httpx.AsyncClient, base_url: str, parsed_base
    ) -> list[str]:
        """Discover pages by following links from the homepage."""
        urls = set()
        to_visit = [base_url]
        visited = set()

        while to_visit and len(urls) < self.max_pages * 2:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "lxml")

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)

                    if parsed.netloc != parsed_base.netloc:
                        continue

                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean_url not in urls and clean_url not in visited:
                        urls.add(clean_url)
                        if len(to_visit) < 50:
                            to_visit.append(clean_url)

            except Exception:
                continue

        return list(urls)
