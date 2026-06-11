"""Entrada das evals PAGAS — com guard de custo.

Comportamento padrao (SEM `--run`): apenas ESTIMA o custo e sai (dry-run, US$ 0,00).
Para executar de verdade:  python eval/run_paga.py --sanity --run   (requer chave no .env)

Flags:
  --sanity   2 casos por categoria (default)
  --full     todos os casos
  --run      executa de fato (chama a API paga). Sem isto, so estima.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "eval"))

import cost  # noqa: E402
import runner_paga  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Evals pagas com guard de custo.")
    ap.add_argument("--sanity", action="store_true", help="2 casos por categoria (default)")
    ap.add_argument("--full", action="store_true", help="todos os casos")
    ap.add_argument("--run", action="store_true", help="EXECUTA de fato (gasta API)")
    args = ap.parse_args()

    sanity = not args.full
    n = runner_paga.contar(sanity)
    est = cost.estimar(n)

    print(f"=== EVALS PAGAS — {'--sanity' if sanity else '--full'} ===")
    print(f"  Dossies: {n}  (1 chamada Haiku por dossie; pre-parecer e' deterministico)")
    print(
        f"  Custo estimado: ~US$ {est['custo_total']:.4f} total "
        f"(~US$ {est['custo_por_dossie']:.4f}/dossie; ~{int(est['in_tok'])} in / {int(est['out_tok'])} out)"
    )
    alvo = "OK" if est["custo_por_dossie"] <= 0.01 else "ACIMA do alvo"
    print(f"  Alvo RNF-01 (<= US$ 0,01/dossie): {alvo}")
    print("  Caveat: estimativa grosseira de tokens; o custo real sai do usage de cada resposta.")

    if not args.run:
        print("\n[DRY-RUN] Nenhuma chamada paga feita. Para executar: adicione --run (requer ANTHROPIC_API_KEY no .env).")
        return 0

    if not runner_paga.tem_chave():
        print("\nERRO: ANTHROPIC_API_KEY ausente no ambiente/.env. Abortado — nada foi gasto.")
        return 2

    print("\nExecutando evals pagas (LLM real)...")
    resultados = runner_paga.rodar(sanity=sanity)
    por_eval: dict[str, list] = {}
    for r in resultados:
        por_eval.setdefault(r["eval_id"], []).append(r)
    todos_ok = True
    for eval_id, rs in por_eval.items():
        ok = sum(1 for r in rs if r["ok"])
        status = "PASS" if ok == len(rs) else "FAIL"
        todos_ok = todos_ok and ok == len(rs)
        print(f"  {eval_id:16} {ok}/{len(rs)} {status}")
        for r in rs:
            if not r["ok"]:
                print(f"      FALHA {r['id']}: {r['detalhe']}")
    print(f"\n  GERAL: {'TODAS PASSARAM' if todos_ok else 'HA FALHAS'}")
    print("  Lembrete: registre o custo real e os caveats em eval/results/RESULTS.md.")
    return 0 if todos_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
