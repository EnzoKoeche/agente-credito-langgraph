"""Motores de OCR (aresta e1).

`OcrEngine` e' um Protocol injetavel. `NoopOcrEngine` (demo) usa o conteudo ja
presente no documento — permite exercitar o ramo de OCR do grafo sem o binario
do sistema. `TesseractOcrEngine` (real) exige `pytesseract` + `tesseract`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..state import Documento


@runtime_checkable
class OcrEngine(Protocol):
    def ocr(self, documento: Documento) -> str: ...


class NoopOcrEngine:
    """OCR no-op para demo/testes: devolve o conteudo existente (ou placeholder)."""

    def ocr(self, documento: Documento) -> str:
        return documento.conteudo or "[OCR indisponivel — sem conteudo]"


class TesseractOcrEngine:
    """OCR real via pytesseract. `documento.conteudo` deve ser o caminho da imagem."""

    def __init__(self, lang: str = "por"):
        self.lang = lang

    def ocr(self, documento: Documento) -> str:
        import pytesseract  # lazy
        from PIL import Image  # lazy

        return pytesseract.image_to_string(
            Image.open(documento.conteudo), lang=self.lang
        )
