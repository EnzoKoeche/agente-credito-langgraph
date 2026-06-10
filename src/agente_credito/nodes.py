"""Nos do grafo e funcoes de roteamento das arestas condicionais.

Cada no recebe `(state, deps)` e devolve um dict parcial de updates. Os nos sao
finos: orquestram tools/seguranca (puras) e os efeitos injetados em `deps`.
Roteadores sao funcoes puras de `state` (faceis de testar — TEST-GRAPH-ROUTE).
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.types import interrupt

from .config import LIMIAR_CONFIANCA
from .deps import Deps
from .security.injection import detectar_injecao
from .security.pii import mascarar_pii
from .state import (
    AnalysisState,
    Decisao,
    DecisaoHumana,
    Formato,
    Indicadores,
    MetadadosAuditoria,
    PreParecer,
)
from .tools.indicadores import (
    capacidade_de_pagamento,
    comprometimento_de_renda,
    simulacao_de_parcela,
)
from .tools.inconsistencias import detectar_inconsistencias


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Nos                                                                          #
# --------------------------------------------------------------------------- #
def no_ingestao(state: AnalysisState, deps: Deps) -> dict:
    """n1 — carrega/normaliza documentos, marca OCR, sinaliza injecao, marca inicio."""
    docs = []
    injecoes = 0
    for d in state.documentos:
        requer = d.formato in (Formato.IMAGEM, Formato.PDF_ESCANEADO)
        docs.append(d.model_copy(update={"requer_ocr": requer}))
        if detectar_injecao(d.conteudo):
            injecoes += 1
    return {
        "documentos": docs,
        "inicio_ts": _agora(),
        "tentativas_injecao": injecoes,
        "trilha": state.trilha + ["ingestao"],
    }


def no_ocr(state: AnalysisState, deps: Deps) -> dict:
    """Ramo da aresta e1 — rasteriza/OCR nos documentos que exigem, via engine injetado."""
    docs = []
    for d in state.documentos:
        if d.requer_ocr:
            texto = deps.ocr_engine.ocr(d)
            docs.append(d.model_copy(update={"conteudo": texto}))
        else:
            docs.append(d)
    return {"documentos": docs, "trilha": state.trilha + ["ocr"]}


def no_extracao(state: AnalysisState, deps: Deps) -> dict:
    """n2 — extracao estruturada via extrator injetado (mock no demo)."""
    dados = deps.extractor.extrair(state.documentos)
    return {
        "dados_extraidos": dados,
        "confianca_extracao": dados.confianca,
        "trilha": state.trilha + ["extracao"],
    }


def no_validacao_confianca(state: AnalysisState, deps: Deps) -> dict:
    """n3 — sinaliza escalacao se confianca < 0,6 (aresta e2)."""
    baixa = state.confianca_extracao is None or state.confianca_extracao < LIMIAR_CONFIANCA
    return {"escalonado": baixa, "trilha": state.trilha + ["validacao_confianca"]}


def no_indicadores(state: AnalysisState, deps: Deps) -> dict:
    """n4 — indicadores via tools deterministicas (nenhum numero vem do LLM)."""
    d = state.dados_extraidos
    comp = cap = parc = None
    if d is not None:
        # Guards uniformes em `is not None`: 0.0 e' valor de dominio legitimo; a
        # positividade e' responsabilidade das tools (que levantam ValueError -> None).
        try:
            if d.soma_parcelas_mensais is not None and d.renda_liquida_mensal is not None:
                comp = comprometimento_de_renda(d.soma_parcelas_mensais, d.renda_liquida_mensal)
        except ValueError:
            comp = None
        try:
            if d.renda_liquida_mensal is not None and d.despesas_fixas_mensais is not None:
                cap = capacidade_de_pagamento(d.renda_liquida_mensal, d.despesas_fixas_mensais)
        except ValueError:
            cap = None
        try:
            if (
                d.valor_credito_solicitado is not None
                and d.taxa_mensal is not None
                and d.n_parcelas is not None
            ):
                parc = simulacao_de_parcela(d.valor_credito_solicitado, d.taxa_mensal, d.n_parcelas)
        except ValueError:
            parc = None
    indicadores = Indicadores(
        comprometimento_de_renda=comp,
        capacidade_de_pagamento=cap,
        parcela_simulada=parc,
    )
    return {"indicadores": indicadores, "trilha": state.trilha + ["indicadores"]}


def no_inconsistencias(state: AnalysisState, deps: Deps) -> dict:
    """n5 — detecta discrepancias entre fontes (RF-04)."""
    pares = state.dados_extraidos.pares_para_conferencia if state.dados_extraidos else []
    incs = detectar_inconsistencias(pares)
    return {"inconsistencias": incs, "trilha": state.trilha + ["inconsistencias"]}


def no_pre_parecer(state: AnalysisState, deps: Deps) -> dict:
    """n6 — rascunho assistivo com fontes citadas; SEM veredito; PII mascarada."""
    ind = state.indicadores
    linhas = ["Pre-parecer (assistivo — nao e' decisao de aprovacao/recusa):"]
    fontes: list[str] = []
    if ind is not None:
        if ind.comprometimento_de_renda is not None:
            linhas.append(
                f"- Comprometimento de renda: {ind.comprometimento_de_renda:.2%} "
                "(fonte: tool indicadores)."
            )
            fontes.append("tool:comprometimento_de_renda")
        if ind.capacidade_de_pagamento is not None:
            linhas.append(
                f"- Capacidade de pagamento: R$ {ind.capacidade_de_pagamento:.2f} "
                "(fonte: tool indicadores)."
            )
            fontes.append("tool:capacidade_de_pagamento")
        if ind.parcela_simulada is not None:
            linhas.append(
                f"- Parcela simulada: R$ {ind.parcela_simulada:.2f} "
                "(fonte: tool simulacao_de_parcela)."
            )
            fontes.append("tool:simulacao_de_parcela")
    for inc in state.inconsistencias:
        rotulo = ", ".join(inc.fontes) or "n/d"
        linhas.append(
            f"- Inconsistencia [{inc.severidade.value}] no campo '{inc.campo}' "
            f"(fontes: {rotulo})."
        )
        fontes.extend(inc.fontes)
    nome = state.dados_extraidos.nome_cliente if state.dados_extraidos else None
    texto = mascarar_pii("\n".join(linhas), nome=nome)
    return {
        "rascunho_pre_parecer": PreParecer(texto=texto, fontes_citadas=fontes),
        "trilha": state.trilha + ["pre_parecer"],
    }


def no_revisao_humana(state: AnalysisState, deps: Deps) -> dict:
    """n7 — INTERRUPT: pausa e espera a decisao humana (aprovar/devolver)."""
    nome = state.dados_extraidos.nome_cliente if state.dados_extraidos else None
    base = (
        state.rascunho_pre_parecer.texto
        if state.rascunho_pre_parecer
        else "(sem pre-parecer — escalonado por baixa confianca)"
    )
    resumo = mascarar_pii(base, nome=nome)
    decisao = interrupt(
        {
            "tipo": "revisao_credito",
            "escalonado_baixa_confianca": state.escalonado,
            "pre_parecer": resumo,
            "instrucao": (
                "Responda com {'decisao': 'aprovado'|'devolvido', 'motivo': str, "
                "'revisor': str}"
            ),
        }
    )
    dh = decisao if isinstance(decisao, DecisaoHumana) else DecisaoHumana(**decisao)
    return {"decisao_humana": dh, "trilha": state.trilha + ["revisao_humana"]}


def no_registro_auditoria(state: AnalysisState, deps: Deps) -> dict:
    """n8 — consolida a trilha de auditoria (PII mascarada; versao prompt/modelo)."""
    nome = state.dados_extraidos.nome_cliente if state.dados_extraidos else None
    base = state.rascunho_pre_parecer.texto if state.rascunho_pre_parecer else ""
    resumo = mascarar_pii(base, nome=nome)
    dh = state.decisao_humana
    metadados = MetadadosAuditoria(
        versao_prompt=deps.versao_prompt,
        versao_modelo=deps.versao_modelo,
        custo_usd=state.custo_usd,
        timestamp_inicio=state.inicio_ts,
        timestamp_fim=_agora(),
        resumo_mascarado=resumo,
        escalonado_baixa_confianca=state.escalonado,
        tentativas_injecao=state.tentativas_injecao,
        decisao=dh.decisao if dh else None,
        # motivo e' texto livre do revisor humano -> mascarar PII antes de persistir (RF-11)
        motivo_decisao=mascarar_pii(dh.motivo, nome=nome) if dh else "",
    )
    return {"metadados": metadados, "trilha": state.trilha + ["registro_auditoria"]}


# --------------------------------------------------------------------------- #
# Roteadores das arestas condicionais (funcoes puras de state)                 #
# --------------------------------------------------------------------------- #
def roteia_ingestao(state: AnalysisState) -> str:
    """e1 — PDF escaneado/imagem -> OCR; senao -> extracao direta."""
    return "ocr" if any(d.requer_ocr for d in state.documentos) else "extracao"


def roteia_confianca(state: AnalysisState) -> str:
    """e2 — confianca < 0,6 -> escalacao direta para revisao_humana; senao -> indicadores."""
    return "revisao_humana" if state.escalonado else "indicadores"


def roteia_revisao(state: AnalysisState) -> str:
    """e3 — aprovado/devolvido (ambos registram auditoria; o rotulo e' o roteado).

    Fail-safe: ausencia de decisao humana e' condicao de erro (premissa P1 — o agente
    nunca decide), jamais um 'aprovado' implicito.
    """
    dh = state.decisao_humana
    if dh is None:
        raise ValueError("roteia_revisao alcancado sem decisao humana (viola P1)")
    return "devolvido" if dh.decisao == Decisao.DEVOLVIDO else "aprovado"
