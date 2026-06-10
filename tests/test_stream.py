"""TEST-STREAM — streaming de progresso do grafo (RF-09, modo updates)."""

from __future__ import annotations

from agente_credito.graph import build_demo_graph
from agente_credito.persistence import sqlite_checkpointer
from agente_credito.state import AnalysisState, Documento, Formato


def test_stream_updates_emite_progresso_dos_nos(dados_consistentes):
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="x")]
    cfg = {"configurable": {"thread_id": "s-1"}}
    vistos: list[str] = []
    with sqlite_checkpointer(":memory:") as cp:
        app = build_demo_graph(dados_consistentes, checkpointer=cp)
        for evento in app.stream(
            AnalysisState(documentos=docs), cfg, stream_mode="updates"
        ):
            vistos.extend(evento.keys())

    # progresso de varios nos do fluxo feliz antes do interrupt
    assert "ingestao" in vistos
    assert "extracao" in vistos
    assert "validacao_confianca" in vistos
    assert "indicadores" in vistos
    assert "pre_parecer" in vistos

    # emitidos na ORDEM do fluxo feliz (pre-interrupt)
    ordem = ["ingestao", "extracao", "validacao_confianca", "indicadores", "pre_parecer"]
    indices = [vistos.index(n) for n in ordem]
    assert indices == sorted(indices)
