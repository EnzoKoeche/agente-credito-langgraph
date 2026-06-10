"""TEST-INCONS-LIMIAR — discrepancia, severidade e bordas 0,30/0,50 (RF-04).

Cobre EVAL-DET-01/02/03/07: consistente, media, alta e bordas exatas (comparacao estrita).
"""

from __future__ import annotations

import pytest

from agente_credito.state import ParConferencia, Severidade
from agente_credito.tools.inconsistencias import (
    classificar_severidade,
    detectar_inconsistencias,
    discrepancia_relativa,
)


def test_discrepancia_relativa():
    assert discrepancia_relativa(100, 70) == pytest.approx(0.30)
    assert discrepancia_relativa(100, 50) == pytest.approx(0.50)
    assert discrepancia_relativa(100, 100) == pytest.approx(0.0)


def test_discrepancia_dado_ausente():
    assert discrepancia_relativa(None, 50) is None
    assert discrepancia_relativa(100, None) is None
    assert discrepancia_relativa(0, 50) is None
    assert discrepancia_relativa(-5, 50) is None


def test_bordas_exatas_comparacao_estrita():
    # 0,30 NAO dispara media; 0,50 NAO dispara alta
    assert classificar_severidade(0.30) == Severidade.CONSISTENTE
    assert classificar_severidade(0.50) == Severidade.MEDIA


def test_severidades_dentro_das_faixas():
    assert classificar_severidade(0.0) == Severidade.CONSISTENTE
    assert classificar_severidade(0.40) == Severidade.MEDIA
    assert classificar_severidade(0.60) == Severidade.ALTA
    assert classificar_severidade(None) == Severidade.DADO_AUSENTE


def test_acima_das_bordas():
    assert classificar_severidade(0.3001) == Severidade.MEDIA
    assert classificar_severidade(0.5001) == Severidade.ALTA


def test_detectar_filtra_consistentes_e_classifica():
    pares = [
        ParConferencia(campo="renda", valor_declarado=100, valor_comprovado=100),    # consistente
        ParConferencia(campo="parcela", valor_declarado=100, valor_comprovado=40),   # alta (0,60)
        ParConferencia(campo="despesa", valor_declarado=None, valor_comprovado=10),  # dado ausente
    ]
    resultado = detectar_inconsistencias(pares)
    por_campo = {i.campo: i.severidade for i in resultado}
    assert "renda" not in por_campo  # consistente foi filtrado
    assert por_campo["parcela"] == Severidade.ALTA
    assert por_campo["despesa"] == Severidade.DADO_AUSENTE

    todos = detectar_inconsistencias(pares, incluir_consistentes=True)
    assert len(todos) == 3
