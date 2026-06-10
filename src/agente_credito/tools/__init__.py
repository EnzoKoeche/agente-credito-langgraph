"""Tools deterministicas: o LLM nunca calcula numero (premissa P2)."""

from .inconsistencias import (
    avaliar_par,
    classificar_severidade,
    detectar_inconsistencias,
    discrepancia_relativa,
)
from .indicadores import (
    capacidade_de_pagamento,
    comprometimento_de_renda,
    simulacao_de_parcela,
)

__all__ = [
    "comprometimento_de_renda",
    "capacidade_de_pagamento",
    "simulacao_de_parcela",
    "discrepancia_relativa",
    "classificar_severidade",
    "avaliar_par",
    "detectar_inconsistencias",
]
