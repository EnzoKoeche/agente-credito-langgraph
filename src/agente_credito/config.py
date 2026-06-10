"""Constantes e versionamento — fonte unica dos numeros do dominio.

Os limiares vivem AQUI para que tools, nos do grafo e testes referenciem o mesmo
valor. Mudar a regra de negocio = mudar uma constante, nunca um literal espalhado.
"""

from __future__ import annotations

import os

# --- Regra de inconsistencia (RF-04) — comparacao ESTRITA com `>` ---
# discrepancia = |declarado - comprovado| / declarado   (declarado > 0)
#   > 0,50          -> ALTA
#   0,30 < d <= 0,50 -> MEDIA
#   <= 0,30         -> CONSISTENTE
LIMIAR_INCONSISTENCIA_MEDIA: float = 0.30
LIMIAR_INCONSISTENCIA_ALTA: float = 0.50

# --- Confianca da extracao (RF-02 / e2) ---
# confianca < 0,6 -> escalacao direta para revisao humana, SEM calculo.
LIMIAR_CONFIANCA: float = 0.60

# --- Versionamento registrado na trilha de auditoria (RF-07) ---
VERSAO_PROMPT: str = "p-1.0.0"
MODELO_PADRAO: str = "claude-haiku-4-5-20251001"  # Haiku: custo baixo (RNF-01)


def modelo_configurado() -> str:
    """Modelo efetivo: env `ANTHROPIC_MODEL` ou o padrao Haiku."""
    return os.getenv("ANTHROPIC_MODEL", MODELO_PADRAO)
