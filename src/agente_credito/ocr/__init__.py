"""OCR pluggable (RF-01 / aresta e1). Default no-op (demo); Tesseract opcional."""

from .engine import NoopOcrEngine, OcrEngine, TesseractOcrEngine

__all__ = ["OcrEngine", "NoopOcrEngine", "TesseractOcrEngine"]
