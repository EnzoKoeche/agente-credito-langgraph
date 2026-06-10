"""TEST-TOOLS-INDIC — comprometimento de renda e capacidade de pagamento (RF-03)."""

from __future__ import annotations

import pytest

from agente_credito.tools.indicadores import (
    capacidade_de_pagamento,
    comprometimento_de_renda,
)


def test_comprometimento_ok():
    assert comprometimento_de_renda(1500, 5000) == pytest.approx(0.30)


def test_comprometimento_renda_zero_ou_none():
    with pytest.raises(ValueError):
        comprometimento_de_renda(1500, 0)
    with pytest.raises(ValueError):
        comprometimento_de_renda(1500, None)


def test_comprometimento_parcela_invalida():
    with pytest.raises(ValueError):
        comprometimento_de_renda(-1, 5000)
    with pytest.raises(ValueError):
        comprometimento_de_renda(None, 5000)


def test_capacidade_ok():
    assert capacidade_de_pagamento(5000, 2000) == pytest.approx(3000)


def test_capacidade_pode_ser_negativa():
    assert capacidade_de_pagamento(2000, 5000) == pytest.approx(-3000)


def test_capacidade_obrigatorios():
    with pytest.raises(ValueError):
        capacidade_de_pagamento(None, 2000)
    with pytest.raises(ValueError):
        capacidade_de_pagamento(5000, None)
