"""Integra as evals gratuitas ao pytest: EVAL-DET-01..07, EVAL-G2, EVAL-G1.

Garante que toda mudanca de regra que quebre uma eval seja pega no CI (sem custo).
"""

from __future__ import annotations

import runner_det
import runner_grafo
import pytest


@pytest.mark.parametrize(
    "resultado", runner_det.rodar_todos(), ids=lambda r: r["eval_id"]
)
def test_eval_deterministica(resultado):
    assert resultado["ok"] == resultado["total"], resultado["falhas"]


def test_eval_g2_roteamento():
    r = runner_grafo.rodar_g2()
    assert r["ok"] == r["total"], r["falhas"]


def test_eval_g1_retomada_identica():
    r = runner_grafo.rodar_g1()
    assert r["ok"] == r["total"], r["detalhe"]
