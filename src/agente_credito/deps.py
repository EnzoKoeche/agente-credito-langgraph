"""Dependencias injetaveis dos nos (extrator, OCR, versionamento).

Mantem os nos finos: a logica pesada vive nas tools/seguranca (puras e testadas),
e os efeitos (LLM, OCR) entram por aqui — o que torna o modo demo trivial.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import VERSAO_PROMPT, modelo_configurado
from .extraction.extractor import Extractor
from .ocr.engine import OcrEngine


@dataclass
class Deps:
    extractor: Extractor
    ocr_engine: OcrEngine
    versao_prompt: str = VERSAO_PROMPT
    versao_modelo: str = ""

    def __post_init__(self) -> None:
        if not self.versao_modelo:
            self.versao_modelo = modelo_configurado()
