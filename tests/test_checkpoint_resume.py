"""TEST-CHECKPOINT-RESUME — retomada pos-interrupt restaura estado identico (RF-08/RNF-06).

Persiste o checkpoint em arquivo, FECHA a sessao, reabre uma NOVA sessao sobre o
mesmo arquivo e verifica que o estado restaurado tem hash identico (EVAL-G1),
retomando ate concluir.
"""

from __future__ import annotations

import hashlib
import json

from langgraph.types import Command

from agente_credito.graph import build_demo_graph
from agente_credito.persistence import sqlite_checkpointer
from agente_credito.state import AnalysisState, Documento, Formato

_CAMPOS_ESTAVEIS = (
    "documentos",
    "dados_extraidos",
    "confianca_extracao",
    "indicadores",
    "inconsistencias",
    "rascunho_pre_parecer",
    "escalonado",
)


def _hash_estado(values: dict) -> str:
    """Hash dos campos estaveis (ignora timestamps/custos volateis de metadados)."""
    relevantes = {campo: values.get(campo) for campo in _CAMPOS_ESTAVEIS}
    serial = json.dumps(relevantes, default=str, sort_keys=True)
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def test_retomada_restaura_estado_identico(dados_consistentes, tmp_path):
    db = str(tmp_path / "cp.sqlite")
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="x")]
    cfg = {"configurable": {"thread_id": "t-resume"}}

    # Sessao 1: roda ate o interrupt e encerra
    with sqlite_checkpointer(db) as cp:
        app = build_demo_graph(dados_consistentes, checkpointer=cp)
        app.invoke(AnalysisState(documentos=docs), cfg)
        snap1 = app.get_state(cfg)
        h1 = _hash_estado(snap1.values)
        assert snap1.next  # ha no pendente (pausado no interrupt)

    # Sessao 2: reabre o MESMO arquivo -> estado identico -> retoma e conclui
    with sqlite_checkpointer(db) as cp2:
        app2 = build_demo_graph(dados_consistentes, checkpointer=cp2)
        snap2 = app2.get_state(cfg)
        h2 = _hash_estado(snap2.values)
        assert h2 == h1  # RNF-06: retomada restaura estado identico
        final = app2.invoke(
            Command(resume={"decisao": "aprovado", "motivo": "ok", "revisor": "ana"}),
            cfg,
        )

    estado = AnalysisState(**final)
    assert estado.metadados is not None
    assert estado.decisao_humana.decisao.value == "aprovado"
    assert estado.trilha[-1] == "registro_auditoria"
