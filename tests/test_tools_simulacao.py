"""TEST-TOOLS-SIMUL — simulacao de parcela pela Tabela Price (RF-03 / EVAL-DET-06)."""

from __future__ import annotations

import pytest

from agente_credito.tools.indicadores import simulacao_de_parcela


def test_price_com_juros():
    pmt = simulacao_de_parcela(10000, 0.02, 24)
    esperado = 10000 * 0.02 / (1 - (1.02) ** -24)
    assert pmt == pytest.approx(esperado)
    assert 528.0 < pmt < 529.0  # sanity numerica


def test_sem_juros_divide_igual():
    assert simulacao_de_parcela(1200, 0.0, 12) == pytest.approx(100.0)


def test_valor_invalido():
    with pytest.raises(ValueError):
        simulacao_de_parcela(0, 0.02, 12)
    with pytest.raises(ValueError):
        simulacao_de_parcela(None, 0.02, 12)


def test_n_parcelas_invalido():
    with pytest.raises(ValueError):
        simulacao_de_parcela(1000, 0.02, 0)
    with pytest.raises(ValueError):
        simulacao_de_parcela(1000, 0.02, None)


def test_taxa_negativa_ou_none():
    with pytest.raises(ValueError):
        simulacao_de_parcela(1000, -0.01, 12)
    with pytest.raises(ValueError):
        simulacao_de_parcela(1000, None, 12)
