"""Runner das evals deterministicas EVAL-DET-01..07.

Le os datasets JSON e roda o codigo de PRODUCAO (tools/nos), comparando a saida
com o `esperado` (gabarito do oracle). Sem chamada de API.
"""

from __future__ import annotations

import json
import pathlib

from agente_credito.nodes import no_validacao_confianca
from agente_credito.state import AnalysisState, ParConferencia
from agente_credito.tools.indicadores import simulacao_de_parcela
from agente_credito.tools.inconsistencias import avaliar_par

_DET = pathlib.Path(__file__).resolve().parent / "datasets" / "det"
_TOL = 1e-6


def _prod_inconsistencia(entrada: dict):
    par = ParConferencia(
        campo="x",
        valor_declarado=entrada["valor_declarado"],
        valor_comprovado=entrada["valor_comprovado"],
    )
    return avaliar_par(par).severidade.value


def _prod_confianca(entrada: dict):
    out = no_validacao_confianca(AnalysisState(confianca_extracao=entrada["confianca"]), None)
    return {"escalona": out["escalonado"]}


def _prod_simulacao(entrada: dict):
    return {"parcela": simulacao_de_parcela(entrada["valor"], entrada["taxa_mensal"], entrada["n_parcelas"])}


def _igual(eval_id: str, esperado, obtido) -> bool:
    if eval_id == "EVAL-DET-06":
        return abs(esperado["parcela"] - obtido["parcela"]) <= _TOL
    return esperado == obtido


def rodar_arquivo(caminho: pathlib.Path) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    eid = dados["eval_id"]
    ok = 0
    falhas = []
    for caso in dados["casos"]:
        entrada = caso["entrada"]
        if eid == "EVAL-DET-05":
            obtido = _prod_confianca(entrada)
        elif eid == "EVAL-DET-06":
            obtido = _prod_simulacao(entrada)
        else:
            obtido = _prod_inconsistencia(entrada)
        if _igual(eid, caso["esperado"], obtido):
            ok += 1
        else:
            falhas.append(
                {"id": caso["id"], "entrada": entrada, "esperado": caso["esperado"], "obtido": obtido}
            )
    return {
        "eval_id": eid,
        "categoria": dados["categoria"],
        "total": len(dados["casos"]),
        "ok": ok,
        "falhas": falhas,
    }


def rodar_todos() -> list[dict]:
    return [rodar_arquivo(f) for f in sorted(_DET.glob("*.json"))]
