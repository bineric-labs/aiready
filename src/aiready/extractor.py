"""Extract main content from HTML pages."""

import re
from bs4 import BeautifulSoup, NavigableString


class ContentExtractor:
    """Extract main content from HTML, stripping navigation and boilerplate."""

    REMOVE_TAGS = [
        "script", "style", "nav", "header", "footer", "aside",
        "noscript", "iframe", "svg", "form", "button",
    ]

    REMOVE_CLASSES = [
        "nav", "navigation", "menu", "sidebar", "footer", "header",
        "breadcrumb", "pagination", "comments", "social", "share",
        "advertisement", "ad", "banner", "cookie", "popup", "modal",
    ]

    MAIN_CONTENT_SELECTORS = [
        "main",
        "article",
        "[role='main']",
        ".content",
        ".post-content",
        ".article-content",
        ".markdown-body",
        ".prose",
        "#content",
        "#main",
    ]

    def extract(self, html: str, source_type: str = "web") -> dict:
        """Extract title and main content from HTML."""
        if source_type == "local" and not html.strip().startswith("<"):
            return self._extract_from_markdown(html)

        return self._extract_from_html(html)

    def _extract_from_html(self, html: str) -> dict:
        """Extract content from HTML."""
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)

        for tag in self.REMOVE_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        for el in soup.find_all(class_=lambda c: c and any(
            cls in str(c).lower() for cls in self.REMOVE_CLASSES
        )):
            el.decompose()

        main_content = None
        for selector in self.MAIN_CONTENT_SELECTORS:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.body or soup

        text = self._get_text(main_content)
        text = self._clean_text(text)

        return {
            "title": title,
            "content": text,
        }

    def _extract_from_markdown(self, content: str) -> dict:
        """Extract content from markdown file."""
        lines = content.strip().split("\n")
        title = ""

        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
            elif line.startswith("---"):
                continue

        if not title and lines:
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith(("---", "#", ">")):
                    title = stripped[:100]
                    break

        return {
            "title": title,
            "content": content,
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            title = re.split(r"\s*[|\-–—]\s*", title)[0].strip()
            return title

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        return ""

    def _get_text(self, element) -> str:
        """Get text content preserving some structure."""
        if element is None:
            return ""

        texts = []
        for child in element.descendants:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    texts.append(text)
            elif child.name in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
                texts.append("\n")

        return " ".join(texts)

    def _clean_text(self, text: str) -> str:
        """Clean up extracted text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                lines.append(line)

        return "\n".join(lines)
