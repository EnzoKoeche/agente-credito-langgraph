"""Degradacao de no_indicadores: tool com entrada invalida -> indicador None (sem quebrar)."""

from __future__ import annotations

from agente_credito.deps import Deps
from agente_credito.extraction.extractor import MockExtractor
from agente_credito.nodes import no_indicadores
from agente_credito.ocr.engine import NoopOcrEngine
from agente_credito.state import AnalysisState, DadosExtraidos


def _deps(dados: DadosExtraidos) -> Deps:
    return Deps(extractor=MockExtractor(dados), ocr_engine=NoopOcrEngine())


def test_indicadores_degenerados_viram_none():
    dados = DadosExtraidos(
        renda_liquida_mensal=0.0,       # invalida -> comprometimento ValueError -> None
        soma_parcelas_mensais=100.0,
        despesas_fixas_mensais=50.0,
        valor_credito_solicitado=-5.0,  # invalido -> simulacao ValueError -> None
        taxa_mensal=0.02,
        n_parcelas=12,
        confianca=0.9,
    )
    out = no_indicadores(AnalysisState(dados_extraidos=dados), _deps(dados))
    ind = out["indicadores"]
    assert ind.comprometimento_de_renda is None
    assert ind.parcela_simulada is None
    assert ind.capacidade_de_pagamento == -50.0  # 0 - 50, valido (pode ser negativo)


def test_indicadores_sem_dados_extraidos():
    dados = DadosExtraidos()
    out = no_indicadores(AnalysisState(), _deps(dados))
    ind = out["indicadores"]
    assert ind.comprometimento_de_renda is None
    assert ind.capacidade_de_pagamento is None
    assert ind.parcela_simulada is None
