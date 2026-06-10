"""Roda TODAS as evals gratuitas (deterministicas + grafo) e atualiza RESULTS.md.

Uso:  python eval/run_all.py
Sem custo de API (extrator mock). Sai com codigo 1 se alguma eval falhar.
"""

from __future__ import annotations

import datetime as _dt
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))   # torna agente_credito importavel standalone
sys.path.insert(0, str(_ROOT / "eval"))  # irmaos: runner_det, runner_grafo, oracle

import runner_det  # noqa: E402
import runner_grafo  # noqa: E402
from agente_credito.config import VERSAO_PROMPT  # noqa: E402

_RESULTS = _ROOT / "eval" / "results" / "RESULTS.md"


def _linha(r: dict) -> str:
    status = "PASS" if r["ok"] == r["total"] else "FAIL"
    return f'| {r["eval_id"]} | {r.get("categoria", "-")} | {r["ok"]}/{r["total"]} | {status} |'


def gerar_results_md(det: list, g2: dict, g1: dict, data: str) -> str:
    linhas = [
        "# Resultados das Evals (curado)",
        "",
        f"- **Data:** {data}",
        f"- **Versao prompt:** `{VERSAO_PROMPT}` · **Modelo:** `mock` (evals gratuitas, sem API)",
        "- **Custo:** US$ 0,00 (extrator mock injetavel; nenhuma chamada paga).",
        "",
        "## Evals deterministicas (gratuitas)",
        "",
        "| Eval | Categoria | Resultado | Status |",
        "|------|-----------|-----------|--------|",
    ]
    linhas += [_linha(r) for r in det]
    linhas += [
        "",
        "## Evals de grafo (gratuitas)",
        "",
        "| Eval | Categoria | Resultado | Status |",
        "|------|-----------|-----------|--------|",
        _linha({**g2, "categoria": "roteamento e1/e2/e3"}),
        _linha({**g1, "categoria": "retomada pos-interrupt (hash igual)"}),
        "",
        "## Caveats honestos",
        "",
        "- **Gabarito derivado das regras** (oracle independente em `eval/oracle.py`). Para "
        "severidade e roteamento, o oracle re-enuncia a regra com literais proprios (pega "
        "divergencia real). Para a Tabela Price (EVAL-DET-06) e o limiar de confianca, oracle e "
        "producao coincidem por construcao -> a eval prova **regressao**, nao correcao independente.",
        "- **Sem API:** estas evals nao exercitam o LLM real. Alucinacao/injecao/PII fim-a-fim "
        "(EVAL-PAGA-*) ficam para a Fase 2, com guard de custo.",
        "- **EVAL-G1** valida a igualdade do estado serializado restaurado do checkpoint; nao prova "
        "ausencia de efeitos colaterais externos.",
        "",
    ]
    return "\n".join(linhas)


def main() -> int:
    det = runner_det.rodar_todos()
    g2 = runner_grafo.rodar_g2()
    g1 = runner_grafo.rodar_g1()
    data = _dt.date.today().isoformat()

    todos = det + [g2, g1]
    print(f"\n=== EVALS GRATUITAS ({data}) ===")
    for r in todos:
        status = "PASS" if r["ok"] == r["total"] else "FAIL"
        print(f'  {r["eval_id"]:14} {r["ok"]}/{r["total"]:<4} {status}')
        for f in r.get("falhas", []):
            print(f"      FALHA: {f}")

    _RESULTS.write_text(gerar_results_md(det, g2, g1, data), encoding="utf-8")
    print(f"\n  RESULTS.md atualizado: {_RESULTS}")

    geral_ok = all(r["ok"] == r["total"] for r in todos)
    print(f'  GERAL: {"TODAS PASSARAM" if geral_ok else "HA FALHAS"}')
    return 0 if geral_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
