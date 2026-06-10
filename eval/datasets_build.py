"""Gera os datasets JSON das evals deterministicas a partir do oracle.

Datasets sao versionados (inspecionaveis) e reprodutiveis: rode
`python eval/datasets_build.py` para regenerar. Sem aleatoriedade (geracao
deterministica), para que o gabarito seja estavel entre execucoes.
"""

from __future__ import annotations

import json
import pathlib

import oracle

_DIR = pathlib.Path(__file__).resolve().parent
_DET = _DIR / "datasets" / "det"
_GRAFO = _DIR / "datasets" / "grafo"


def _escrever(caminho: pathlib.Path, payload: dict) -> None:
    caminho.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _inc(eval_id: str, categoria: str, pares: list[tuple]) -> dict:
    """Monta dataset de inconsistencia: cada caso tem (declarado, comprovado) + esperado do oracle."""
    casos = []
    for i, (dec, comp) in enumerate(pares):
        casos.append(
            {
                "id": f"{eval_id}-{i:02d}",
                "entrada": {"valor_declarado": dec, "valor_comprovado": comp},
                "esperado": oracle.severidade_esperada(dec, comp),
            }
        )
    return {"eval_id": eval_id, "categoria": categoria, "casos": casos}


def build_consistente() -> dict:
    # d em [0, 0,30] -> consistente (inclui a borda exata 0,30 em k=23)
    base = 1000.0
    pares = [(base, base * (1 - 0.30 * k / 23)) for k in range(24)]
    return _inc("EVAL-DET-01", "consistente", pares)


def build_media() -> dict:
    # d em (0,30, 0,50] -> media (inclui a borda exata 0,50 em k=23)
    base = 1000.0
    pares = [(base, base * (1 - (0.30 + 0.20 * (k + 1) / 24))) for k in range(24)]
    return _inc("EVAL-DET-02", "media", pares)


def build_alta() -> dict:
    # d em (0,50, ~0,95] -> alta
    base = 1000.0
    pares = [(base, base * (1 - (0.50 + 0.45 * (k + 1) / 24))) for k in range(24)]
    return _inc("EVAL-DET-03", "alta", pares)


def build_dado_ausente() -> dict:
    # declarado/comprovado ausente ou declarado <= 0 -> dado_ausente
    padroes = [
        (None, 100.0),
        (100.0, None),
        (0.0, 100.0),
        (-50.0, 100.0),
        (None, None),
        (-1.0, -1.0),
    ]
    pares = [padroes[k % len(padroes)] for k in range(24)]
    return _inc("EVAL-DET-04", "dado_ausente", pares)


def build_bordas() -> dict:
    # Bordas exatas 0,30/0,50 + vizinhos + casos com ruido de float (1.0/0.7 etc.)
    pares = []
    # exatos 0,30 (consistente) e 0,50 (media), escalados (gera variedade de float)
    for base in (100.0, 1.0, 2.0, 3.0, 7.0, 13.0):
        pares.append((base, base * 0.70))  # d == 0,30 -> consistente
        pares.append((base, base * 0.50))  # d == 0,50 -> media
    # vizinhancas estritas
    pares += [
        (10000.0, 7001.0),   # d = 0,2999 -> consistente
        (10000.0, 6999.0),   # d = 0,3001 -> media
        (10000.0, 5001.0),   # d = 0,4999 -> media
        (10000.0, 4999.0),   # d = 0,5001 -> alta
        (1.0, 0.7),          # float: 0.30000000000000004 -> consistente
        (4.0, 2.8),          # float: 0.30000000000000004 -> consistente
        (1.0, 0.5),          # 0,50 -> media
        (1.0, 0.4),          # 0,60 -> alta
    ]
    return _inc("EVAL-DET-07", "bordas", pares)


def build_baixa_confianca() -> dict:
    # confianca de 0,0 a 1,0 (24 passos) + None -> escalona? (e2)
    casos = []
    valores = [round(k / 23, 4) for k in range(24)]
    valores[12] = 0.60  # garante a borda exata 0,60 (nao escalona, comparacao estrita)
    valores.append(None)
    for i, c in enumerate(valores):
        casos.append(
            {
                "id": f"EVAL-DET-05-{i:02d}",
                "entrada": {"confianca": c},
                "esperado": {"escalona": oracle.escalonamento_esperado(c)},
            }
        )
    return {"eval_id": "EVAL-DET-05", "categoria": "baixa_confianca", "casos": casos}


def build_simulacao() -> dict:
    # (valor, taxa_mensal, n_parcelas) -> parcela esperada (inclui i == 0)
    triples = []
    for k in range(24):
        valor = 1000.0 + 500.0 * k
        i = 0.0 if k % 8 == 0 else round(0.005 + 0.0025 * k, 5)
        n = 6 + k
        triples.append((valor, i, n))
    casos = []
    for idx, (valor, i, n) in enumerate(triples):
        casos.append(
            {
                "id": f"EVAL-DET-06-{idx:02d}",
                "entrada": {"valor": valor, "taxa_mensal": i, "n_parcelas": n},
                "esperado": {"parcela": oracle.parcela_esperada(valor, i, n)},
            }
        )
    return {"eval_id": "EVAL-DET-06", "categoria": "simulacao", "casos": casos}


def build_grafo_e123() -> dict:
    casos = []
    # e1 — por formato
    for fmt in ("txt", "pdf_texto", "pdf_escaneado", "imagem", "imagem", "txt"):
        casos.append(
            {
                "id": f"e1-{fmt}-{len(casos):02d}",
                "aresta": "e1",
                "entrada": {"formato": fmt},
                "esperado": oracle.rota_e1_esperada(fmt),
            }
        )
    # e2 — por confianca (inclui borda 0,60 e None)
    for c in (0.0, 0.3, 0.59, 0.60, 0.61, 0.95, None):
        casos.append(
            {
                "id": f"e2-{c}-{len(casos):02d}",
                "aresta": "e2",
                "entrada": {"confianca": c},
                "esperado": oracle.rota_e2_esperada(c),
            }
        )
    # e3 — por decisao
    for dec in ("aprovado", "devolvido", "aprovado", "devolvido"):
        casos.append(
            {
                "id": f"e3-{dec}-{len(casos):02d}",
                "aresta": "e3",
                "entrada": {"decisao": dec},
                "esperado": oracle.rota_e3_esperada(dec),
            }
        )
    return {"eval_id": "EVAL-G2", "categoria": "roteamento_arestas", "casos": casos}


def main() -> None:
    _escrever(_DET / "EVAL-DET-01.json", build_consistente())
    _escrever(_DET / "EVAL-DET-02.json", build_media())
    _escrever(_DET / "EVAL-DET-03.json", build_alta())
    _escrever(_DET / "EVAL-DET-04.json", build_dado_ausente())
    _escrever(_DET / "EVAL-DET-05.json", build_baixa_confianca())
    _escrever(_DET / "EVAL-DET-06.json", build_simulacao())
    _escrever(_DET / "EVAL-DET-07.json", build_bordas())
    _escrever(_GRAFO / "EVAL-G2.json", build_grafo_e123())
    print("datasets gerados em", _DET, "e", _GRAFO)


if __name__ == "__main__":
    main()
