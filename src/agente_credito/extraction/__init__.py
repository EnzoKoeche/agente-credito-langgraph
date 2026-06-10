"""Extracao estruturada (RF-02). Extrator e' injetavel: mock (demo) ou Anthropic (real)."""

from .extractor import AnthropicExtractor, Extractor, MockExtractor

__all__ = ["Extractor", "MockExtractor", "AnthropicExtractor"]
