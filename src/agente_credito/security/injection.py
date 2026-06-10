"""Defesa contra prompt injection (RF-10): conteudo de documento e DADO.

A defesa e' estrutural: todo conteudo de documento e' envolvido em delimitadores
explicitos e enviado ao LLM na posicao de DADO, nunca de instrucao. `detectar_injecao`
apenas SINALIZA tentativas para a trilha de auditoria — a robustez nao depende da
deteccao, e sim de jamais tratar o conteudo como instrucao.
"""

from __future__ import annotations

import re

_PADROES_INJECAO = [
    re.compile(r"ignore\s+(as\s+)?(regras|instru\w+|tudo)", re.IGNORECASE),
    re.compile(r"desconsidere\s+(as\s+)?(regras|instru\w+)", re.IGNORECASE),
    re.compile(r"aprove\s+(este|esse|o)\s+cr[eé]dito", re.IGNORECASE),
    re.compile(r"aprove\s+automaticamente", re.IGNORECASE),
    re.compile(r"revele\s+(o\s+)?(prompt|sistema|instru\w+)", re.IGNORECASE),
    re.compile(r"voc[eê]\s+(deve|tem que|precisa)\s+aprovar", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
]

DELIM_INI = "<<<DOCUMENTO_INICIO>>>"
DELIM_FIM = "<<<DOCUMENTO_FIM>>>"


def detectar_injecao(texto: str | None) -> bool:
    """True se o texto contiver um padrao conhecido de tentativa de injecao."""
    if not texto:
        return False
    return any(p.search(texto) for p in _PADROES_INJECAO)


def contar_injecoes(textos: list[str]) -> int:
    """Quantos textos disparam a deteccao de injecao (para auditoria)."""
    return sum(1 for t in textos if detectar_injecao(t))


def como_dado(texto: str | None) -> str:
    """Envolve o conteudo em delimitadores de DADO, neutralizando fechamentos forjados."""
    if texto is None:
        texto = ""
    seguro = texto.replace(DELIM_FIM, "").replace(DELIM_INI, "")
    return f"{DELIM_INI}\n{seguro}\n{DELIM_FIM}"
