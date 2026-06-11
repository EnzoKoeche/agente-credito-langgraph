"""Evals pagas no pytest — OPT-IN explicito: so rodam com RUN_EVAL_PAGA=1 + chave.

Sem o opt-in, `pytest` completo nunca gasta — mesmo com ANTHROPIC_API_KEY no .env.
Para rodar de fato (~US$ 0,02, conjunto --sanity de 2 casos/categoria):
    RUN_EVAL_PAGA=1 pytest tests/test_evals_paga.py
"""

from __future__ import annotations

import os

import pytest

import runner_paga  # importa antes do getenv: o load_dotenv() dele carrega o .env

_OPT_IN = os.getenv("RUN_EVAL_PAGA") == "1"


@pytest.mark.skipif(
    not (_OPT_IN and runner_paga.tem_chave()),
    reason="eval paga e' opt-in: exige RUN_EVAL_PAGA=1 e ANTHROPIC_API_KEY (evita gasto acidental)",
)
def test_paga_sanity():
    resultados = runner_paga.rodar(sanity=True)
    falhas = [r for r in resultados if not r["ok"]]
    assert not falhas, falhas
