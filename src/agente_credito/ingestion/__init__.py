"""Ingestao e deteccao de formato (RF-01 / no n1)."""

from .loader import (
    detectar_formato_por_nome,
    marcar_requer_ocr,
    pdf_tem_camada_texto,
)

__all__ = [
    "detectar_formato_por_nome",
    "marcar_requer_ocr",
    "pdf_tem_camada_texto",
]
