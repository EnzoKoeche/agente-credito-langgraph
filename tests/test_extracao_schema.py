"""TEST-EXTRACAO-SCHEMA — validacao Pydantic e extrator mock (RF-02 / EVAL-DET-04)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agente_credito.extraction.extractor import MockExtractor
from agente_credito.state import DadosExtraidos, Documento, Formato


def test_schema_valido():
    d = DadosExtraidos(renda_liquida_mensal=5000, confianca=0.9)
    assert d.renda_liquida_mensal == 5000
    assert d.pares_para_conferencia == []


def test_schema_rejeita_tipo_invalido():
    with pytest.raises(ValidationError):
        DadosExtraidos(renda_liquida_mensal="nao-numerico")


def test_dado_ausente_nao_quebra_schema():
    # Campos ausentes viram None (e nao um valor inventado).
    d = DadosExtraidos(confianca=0.7)
    assert d.renda_liquida_mensal is None
    assert d.soma_parcelas_mensais is None


def test_mock_extractor_retorna_copia(dados_consistentes):
    mock = MockExtractor(dados_consistentes)
    saida = mock.extrair([Documento(nome="x.txt", formato=Formato.TXT)])
    assert saida == dados_consistentes
    assert saida is not dados_consistentes  # copia profunda, nao a mesma instancia
