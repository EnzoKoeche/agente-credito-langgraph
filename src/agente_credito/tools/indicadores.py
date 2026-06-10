"""Indicadores de credito — tools deterministicas (RF-03).

Todas as funcoes sao puras e levantam `ValueError` em entradas degeneradas,
para que o erro seja explicito (e nao um numero silenciosamente errado).
"""

from __future__ import annotations


def comprometimento_de_renda(
    soma_parcelas_mensais: float, renda_liquida_mensal: float
) -> float:
    """Fracao da renda liquida comprometida com parcelas.

    `comprometimento = soma_parcelas_mensais / renda_liquida_mensal`.
    """
    if renda_liquida_mensal is None or renda_liquida_mensal <= 0:
        raise ValueError("renda_liquida_mensal deve ser > 0")
    if soma_parcelas_mensais is None or soma_parcelas_mensais < 0:
        raise ValueError("soma_parcelas_mensais deve ser >= 0")
    return soma_parcelas_mensais / renda_liquida_mensal


def capacidade_de_pagamento(
    renda_liquida_mensal: float, despesas_fixas_mensais: float
) -> float:
    """Sobra mensal: `renda_liquida_mensal - despesas_fixas_mensais`."""
    if renda_liquida_mensal is None or despesas_fixas_mensais is None:
        raise ValueError("renda e despesas sao obrigatorias")
    return renda_liquida_mensal - despesas_fixas_mensais


def simulacao_de_parcela(
    valor: float, taxa_mensal: float, n_parcelas: int
) -> float:
    """Parcela pela Tabela Price (PMT).

    `PMT = valor * i / (1 - (1 + i)^(-n))`, com `i = taxa_mensal`, `n = n_parcelas`.
    Caso degenerado `i == 0` (sem juros): `PMT = valor / n`.
    """
    if valor is None or valor <= 0:
        raise ValueError("valor deve ser > 0")
    if n_parcelas is None or n_parcelas <= 0:
        raise ValueError("n_parcelas deve ser > 0")
    if taxa_mensal is None or taxa_mensal < 0:
        raise ValueError("taxa_mensal deve ser >= 0")
    if taxa_mensal == 0:
        return valor / n_parcelas
    i = taxa_mensal
    return valor * i / (1 - (1 + i) ** (-n_parcelas))
