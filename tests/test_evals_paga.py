"""Evals pagas no pytest — SEMPRE puladas sem ANTHROPIC_API_KEY (CI nao gasta).

Com a chave presente no ambiente/.env, roda o conjunto --sanity (2 casos/categoria).
"""

from __future__ import annotations

import pytest

import runner_paga


@pytest.mark.skipif(
    not runner_paga.tem_chave(),
    reason="sem ANTHROPIC_API_KEY: eval paga nao roda (evita custo no CI)",
)
def test_paga_sanity():
    resultados = runner_paga.rodar(sanity=True)
    falhas = [r for r in resultados if not r["ok"]]
    assert not falhas, falhas
