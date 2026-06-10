"""Mascaramento de PII para logs e trilha de auditoria (RF-11 / RNF-03).

Cobre os padroes definidos (CPF, e-mail, telefone) e o nome do cliente quando
conhecido. Caveat honesto: cobre os padroes abaixo, nao toda PII concebivel.
"""

from __future__ import annotations

import re

# CPF: 11 digitos, com pontuacao opcional (123.456.789-00 ou 12345678900)
_CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# Telefone BR: DDD opcional + 8/9 digitos, pontuacao opcional
_TEL_RE = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")

_CPF_MASK = "***.***.***-**"


def mascarar_pii(texto: str | None, nome: str | None = None) -> str:
    """Mascara CPF, e-mail, telefone e (se fornecido) o nome do cliente.

    A ordem importa: CPF antes de telefone (um CPF e' sequencia longa de digitos
    que o padrao de telefone tambem casaria).
    """
    if not texto:
        return ""
    resultado = texto
    if nome:
        resultado = re.sub(re.escape(nome), "[NOME]", resultado, flags=re.IGNORECASE)
    resultado = _CPF_RE.sub(_CPF_MASK, resultado)
    resultado = _EMAIL_RE.sub("[EMAIL]", resultado)
    resultado = _TEL_RE.sub("[TELEFONE]", resultado)
    return resultado


def contem_pii(texto: str | None) -> bool:
    """True se o texto contiver CPF ou e-mail em claro (deteccao para auditoria)."""
    if not texto:
        return False
    return bool(_CPF_RE.search(texto) or _EMAIL_RE.search(texto))
