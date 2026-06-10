"""Deteccao de formato e marcacao de necessidade de OCR (no n1 / aresta e1)."""

from __future__ import annotations

from pathlib import Path

from ..state import Documento, Formato

_EXT_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


def detectar_formato_por_nome(nome: str) -> Formato:
    """Formato a partir da extensao. PDF assume `PDF_TEXTO` ate prova em contrario."""
    ext = Path(nome).suffix.lower()
    if ext in _EXT_IMAGEM:
        return Formato.IMAGEM
    if ext == ".pdf":
        return Formato.PDF_TEXTO
    return Formato.TXT


def marcar_requer_ocr(doc: Documento) -> Documento:
    """Marca `requer_ocr` para imagem ou PDF escaneado."""
    requer = doc.formato in (Formato.IMAGEM, Formato.PDF_ESCANEADO)
    return doc.model_copy(update={"requer_ocr": requer})


def pdf_tem_camada_texto(caminho: str) -> bool:
    """True se algum texto extraivel existir no PDF (caminho real, exige pypdf)."""
    from pypdf import PdfReader  # lazy

    reader = PdfReader(caminho)
    for pagina in reader.pages:
        if (pagina.extract_text() or "").strip():
            return True
    return False
