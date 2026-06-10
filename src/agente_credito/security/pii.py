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


def _padrao_nome(nome: str) -> re.Pattern | None:
    """Regex do nome com fronteiras de palavra e espacos normalizados.

    Evita over-match (`Ana` dentro de `Mariana`/`analisado`) via `\\b`, e tolera
    espacamento variavel entre os tokens via `\\s+`.
    """
    tokens = [re.escape(t) for t in nome.split()]
    if not tokens:
        return None
    return re.compile(r"\b" + r"\s+".join(tokens) + r"\b", re.IGNORECASE)


def mascarar_pii(texto: str | None, nome: str | None = None) -> str:
    """Mascara nome (se fornecido), CPF, e-mail e telefone.

    Ordem importa: nome primeiro; depois CPF antes de telefone (um CPF e' sequencia
    longa de digitos que o padrao de telefone tambem casaria).
    """
    if not texto:
        return ""
    resultado = texto
    if nome:
        padrao = _padrao_nome(nome)
        if padrao is not None:
            resultado = padrao.sub("[NOME]", resultado)
    resultado = _CPF_RE.sub(_CPF_MASK, resultado)
    resultado = _EMAIL_RE.sub("[EMAIL]", resultado)
    resultado = _TEL_RE.sub("[TELEFONE]", resultado)
    return resultado


def contem_pii(texto: str | None) -> bool:
    """True se o texto contiver CPF, e-mail ou telefone em claro (sinal de auditoria).

    Coerente com o que `mascarar_pii` mascara (exceto nome, que exige o valor
    conhecido). Conservador: prefere falso-positivo a deixar PII passar num gate.
    """
    if not texto:
        return False
    return bool(
        _CPF_RE.search(texto) or _EMAIL_RE.search(texto) or _TEL_RE.search(texto)
    )
