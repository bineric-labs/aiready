"""aiready: Make your site AI ready."""

__version__ = "0.1.0"

from .generator import LLMSTxtGenerator
from .crawler import Crawler
from .extractor import ContentExtractor

__all__ = ["LLMSTxtGenerator", "Crawler", "ContentExtractor"]
