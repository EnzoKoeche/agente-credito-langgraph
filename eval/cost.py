"""Estimativa de custo das evals pagas (Haiku 4.5).

Precos consultados na referencia da API (nao de memoria):
  claude-haiku-4-5 -> input US$ 1,00 / output US$ 5,00 por 1M tokens.
  Prompt caching: leitura ~US$ 0,10/MTok, escrita 5min ~US$ 1,25/MTok.
"""

from __future__ import annotations

HAIKU_INPUT_USD_MTOK = 1.00
HAIKU_OUTPUT_USD_MTOK = 5.00
HAIKU_CACHE_READ_USD_MTOK = 0.10
HAIKU_CACHE_WRITE_USD_MTOK = 1.25


def custo_dossie(in_tok: float, out_tok: float, cache_read_tok: float = 0.0) -> float:
    """Custo de UM dossie: 1 chamada de extracao (o pre-parecer e' deterministico)."""
    return (
        in_tok / 1e6 * HAIKU_INPUT_USD_MTOK
        + out_tok / 1e6 * HAIKU_OUTPUT_USD_MTOK
        + cache_read_tok / 1e6 * HAIKU_CACHE_READ_USD_MTOK
    )


def estimar(n_dossies: int, in_tok: float = 2000, out_tok: float = 300) -> dict:
    """Estimativa grosseira. in/out por dossie sao defaults conservadores (caveat)."""
    por = custo_dossie(in_tok, out_tok)
    return {
        "n_dossies": n_dossies,
        "in_tok": in_tok,
        "out_tok": out_tok,
        "custo_por_dossie": por,
        "custo_total": por * n_dossies,
    }
