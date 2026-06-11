"""Cenarios sinteticos de demonstracao (modo demo, sem custo de API).

Cada cenario devolve (DadosExtraidos, [Documento]) e exercita um caminho distinto
do grafo: aprovavel, inconsistencia alta e baixa confianca (escala direto).
"""

from __future__ import annotations

from agente_credito.state import DadosExtraidos, Documento, Formato, ParConferencia


def _doc(nome: str = "dossie.txt") -> Documento:
    return Documento(nome=nome, formato=Formato.TXT, conteudo="Dossie sintetico de demonstracao.")


def cenario_aprovavel() -> tuple[DadosExtraidos, list[Documento]]:
    """Confianca alta, renda consistente entre fontes -> fluxo feliz completo."""
    dados = DadosExtraidos(
        renda_liquida_mensal=6000.0,
        despesas_fixas_mensais=2500.0,
        soma_parcelas_mensais=1200.0,
        valor_credito_solicitado=12000.0,
        taxa_mensal=0.019,
        n_parcelas=24,
        nome_cliente="Maria Souza",
        cpf="111.222.333-44",
        confianca=0.95,
        pares_para_conferencia=[
            ParConferencia(
                campo="renda",
                valor_declarado=6000.0,
                valor_comprovado=6000.0,
                fonte_declarado="ficha_proposta",
                fonte_comprovado="holerite",
            )
        ],
    )
    return dados, [_doc()]


def cenario_inconsistencia() -> tuple[DadosExtraidos, list[Documento]]:
    """Renda declarada 8000 vs comprovada 3500 -> discrepancia ~0,56 -> severidade ALTA."""
    dados = DadosExtraidos(
        renda_liquida_mensal=8000.0,
        despesas_fixas_mensais=3000.0,
        soma_parcelas_mensais=2000.0,
        valor_credito_solicitado=20000.0,
        taxa_mensal=0.025,
        n_parcelas=36,
        nome_cliente="Joao Lima",
        cpf="222.333.444-55",
        confianca=0.9,
        pares_para_conferencia=[
            ParConferencia(
                campo="renda",
                valor_declarado=8000.0,
                valor_comprovado=3500.0,
                fonte_declarado="ficha_proposta",
                fonte_comprovado="holerite",
            )
        ],
    )
    return dados, [_doc()]


def cenario_baixa_confianca() -> tuple[DadosExtraidos, list[Documento]]:
    """Confianca 0,4 (< 0,6) -> escala direto para revisao, sem calculo (aresta e2)."""
    dados = DadosExtraidos(
        renda_liquida_mensal=4000.0,
        despesas_fixas_mensais=1500.0,
        soma_parcelas_mensais=900.0,
        valor_credito_solicitado=8000.0,
        taxa_mensal=0.02,
        n_parcelas=18,
        nome_cliente="Ana Reis",
        cpf="333.444.555-66",
        confianca=0.4,
    )
    return dados, [_doc()]


CENARIOS = {
    "Aprovavel (consistente)": cenario_aprovavel,
    "Inconsistencia alta (renda)": cenario_inconsistencia,
    "Baixa confianca (escala direto)": cenario_baixa_confianca,
}
