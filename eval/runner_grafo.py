"""Runner das evals de grafo: EVAL-G2 (roteamento) e EVAL-G1 (retomada identica).

Exercita o codigo de PRODUCAO (nos + roteadores + grafo compilado com SqliteSaver).
Sem chamada de API (extrator mock via build_demo_graph).
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile

from langgraph.types import Command

from agente_credito.graph import build_demo_graph
from agente_credito.persistence import sqlite_checkpointer
from agente_credito.nodes import (
    no_ingestao,
    no_validacao_confianca,
    roteia_confianca,
    roteia_ingestao,
    roteia_revisao,
)
from agente_credito.state import (
    AnalysisState,
    DadosExtraidos,
    Decisao,
    DecisaoHumana,
    Documento,
    Formato,
)

_GRAFO = pathlib.Path(__file__).resolve().parent / "datasets" / "grafo"
_CAMPOS = (
    "documentos",
    "dados_extraidos",
    "confianca_extracao",
    "indicadores",
    "inconsistencias",
    "rascunho_pre_parecer",
    "escalonado",
)


# ----------------------------- EVAL-G2 ----------------------------- #
def _rota_e1(formato: str) -> str:
    doc = Documento(nome=f"d.{formato}", formato=Formato(formato), conteudo="x")
    st = AnalysisState(documentos=[doc])
    st2 = st.model_copy(update=no_ingestao(st, None))
    return roteia_ingestao(st2)


def _rota_e2(confianca) -> str:
    st = AnalysisState(confianca_extracao=confianca)
    st2 = st.model_copy(update=no_validacao_confianca(st, None))
    return roteia_confianca(st2)


def _rota_e3(decisao: str) -> str:
    st = AnalysisState(decisao_humana=DecisaoHumana(decisao=Decisao(decisao)))
    return roteia_revisao(st)


def rodar_g2() -> dict:
    dados = json.loads((_GRAFO / "EVAL-G2.json").read_text(encoding="utf-8"))
    ok = 0
    falhas = []
    for caso in dados["casos"]:
        aresta, entrada = caso["aresta"], caso["entrada"]
        if aresta == "e1":
            obtido = _rota_e1(entrada["formato"])
        elif aresta == "e2":
            obtido = _rota_e2(entrada["confianca"])
        else:
            obtido = _rota_e3(entrada["decisao"])
        if obtido == caso["esperado"]:
            ok += 1
        else:
            falhas.append({"id": caso["id"], "esperado": caso["esperado"], "obtido": obtido})
    return {"eval_id": "EVAL-G2", "total": len(dados["casos"]), "ok": ok, "falhas": falhas}


# ----------------------------- EVAL-G1 ----------------------------- #
def _hash_estado(values: dict) -> str:
    relevantes = {campo: values.get(campo) for campo in _CAMPOS}
    return hashlib.sha256(
        json.dumps(relevantes, default=str, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _dados_demo() -> DadosExtraidos:
    return DadosExtraidos(
        renda_liquida_mensal=5000.0,
        despesas_fixas_mensais=2000.0,
        soma_parcelas_mensais=1500.0,
        valor_credito_solicitado=10000.0,
        taxa_mensal=0.02,
        n_parcelas=24,
        nome_cliente="Cliente Demo",
        cpf="123.456.789-00",
        confianca=0.95,
    )


def rodar_g1() -> dict:
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="x")]
    cfg = {"configurable": {"thread_id": "eval-g1"}}
    dados = _dados_demo()
    fd, db = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        # Sessao 1: roda ate o interrupt e fecha
        with sqlite_checkpointer(db) as cp:
            app = build_demo_graph(dados, checkpointer=cp)
            app.invoke(AnalysisState(documentos=docs), cfg)
            snap1 = app.get_state(cfg)
            h1 = _hash_estado(snap1.values)
            pausou = bool(snap1.next)
        # Sessao 2: reabre o mesmo arquivo, compara hash e retoma
        with sqlite_checkpointer(db) as cp2:
            app2 = build_demo_graph(dados, checkpointer=cp2)
            snap2 = app2.get_state(cfg)
            h2 = _hash_estado(snap2.values)
            final = app2.invoke(
                Command(resume={"decisao": "aprovado", "motivo": "ok", "revisor": "demo"}), cfg
            )
        estado = AnalysisState(**final)
        concluiu = estado.trilha[-1] == "registro_auditoria"
        ok = pausou and (h1 == h2) and estado.metadados is not None and concluiu
        return {
            "eval_id": "EVAL-G1",
            "total": 1,
            "ok": 1 if ok else 0,
            "detalhe": {"pausou": pausou, "hash_igual": h1 == h2, "concluiu": concluiu},
        }
    finally:
        for ext in ("", "-wal", "-shm"):
            try:
                os.remove(db + ext)
            except OSError:
                pass
