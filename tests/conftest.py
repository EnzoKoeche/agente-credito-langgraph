"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import pytest

from agente_credito.state import (
    DadosExtraidos,
    Documento,
    Formato,
    ParConferencia,
)


@pytest.fixture
def dados_consistentes() -> DadosExtraidos:
    """Dossie sintetico, confianca alta, sem inconsistencia relevante."""
    return DadosExtraidos(
        renda_liquida_mensal=5000.0,
        despesas_fixas_mensais=2000.0,
        soma_parcelas_mensais=1500.0,
        valor_credito_solicitado=10000.0,
        taxa_mensal=0.02,
        n_parcelas=24,
        nome_cliente="Joao da Silva",
        cpf="123.456.789-00",
        confianca=0.95,
        pares_para_conferencia=[
            ParConferencia(
                campo="renda",
                valor_declarado=5000.0,
                valor_comprovado=5000.0,
                fonte_declarado="ficha_proposta",
                fonte_comprovado="holerite",
            )
        ],
    )


@pytest.fixture
def doc_txt() -> Documento:
    return Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="renda mensal 5000")
