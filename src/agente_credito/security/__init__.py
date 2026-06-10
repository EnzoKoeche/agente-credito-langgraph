"""Seguranca: mascaramento de PII (RF-11) e defesa contra injecao (RF-10)."""

from .injection import como_dado, contar_injecoes, detectar_injecao
from .pii import contem_pii, mascarar_pii

__all__ = [
    "mascarar_pii",
    "contem_pii",
    "detectar_injecao",
    "contar_injecoes",
    "como_dado",
]
