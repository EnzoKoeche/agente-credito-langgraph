"""Deteccao de inconsistencias por discrepancia relativa entre fontes (RF-04).

Regra (comparacao ESTRITA com `>`):
    discrepancia = |declarado - comprovado| / declarado     (declarado > 0)
    > 0,50            -> ALTA
    0,30 < d <= 0,50  -> MEDIA
    <= 0,30           -> CONSISTENTE
    declarado/comprovado ausente OU declarado <= 0 -> DADO_AUSENTE

Bordas exatas (casos de teste obrigatorios):
    d == 0,30 -> CONSISTENTE  |  d == 0,50 -> MEDIA
"""

from __future__ import annotations

from ..config import LIMIAR_INCONSISTENCIA_ALTA, LIMIAR_INCONSISTENCIA_MEDIA
from ..state import Inconsistencia, ParConferencia, Severidade


def discrepancia_relativa(
    valor_declarado: float | None, valor_comprovado: float | None
) -> float | None:
    """Discrepancia relativa, ou `None` quando indeterminavel (dado ausente)."""
    if valor_declarado is None or valor_comprovado is None:
        return None
    if valor_declarado <= 0:
        return None
    return abs(valor_declarado - valor_comprovado) / valor_declarado


def classificar_severidade(discrepancia: float | None) -> Severidade:
    """Classifica a severidade a partir da discrepancia (comparacao estrita)."""
    if discrepancia is None:
        return Severidade.DADO_AUSENTE
    if discrepancia > LIMIAR_INCONSISTENCIA_ALTA:
        return Severidade.ALTA
    if discrepancia > LIMIAR_INCONSISTENCIA_MEDIA:
        return Severidade.MEDIA
    return Severidade.CONSISTENTE


def avaliar_par(par: ParConferencia) -> Inconsistencia:
    """Avalia um par (declarado, comprovado) e retorna a inconsistencia classificada."""
    d = discrepancia_relativa(par.valor_declarado, par.valor_comprovado)
    severidade = classificar_severidade(d)
    fontes = [f for f in (par.fonte_declarado, par.fonte_comprovado) if f]
    return Inconsistencia(
        campo=par.campo,
        valor_declarado=par.valor_declarado,
        valor_comprovado=par.valor_comprovado,
        discrepancia=d,
        severidade=severidade,
        fontes=fontes,
    )


def detectar_inconsistencias(
    pares: list[ParConferencia], incluir_consistentes: bool = False
) -> list[Inconsistencia]:
    """Avalia todos os pares.

    Por padrao retorna apenas os que NAO sao consistentes (media, alta ou
    dado ausente). Com `incluir_consistentes=True`, retorna todos.
    """
    avaliados = [avaliar_par(p) for p in pares]
    if incluir_consistentes:
        return avaliados
    return [i for i in avaliados if i.severidade != Severidade.CONSISTENTE]
