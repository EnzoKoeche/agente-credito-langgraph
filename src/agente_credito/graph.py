"""Montagem do StateGraph: nos, arestas condicionais, interrupt e checkpointing.

Fluxo feliz:
    START -> ingestao -> [e1] -> (ocr ->) extracao -> validacao_confianca -> [e2]
          -> indicadores -> inconsistencias -> pre_parecer -> revisao_humana (interrupt)
          -> [e3] -> registro_auditoria -> END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from . import nodes
from .deps import Deps
from .extraction.extractor import MockExtractor
from .ocr.engine import NoopOcrEngine
from .state import AnalysisState, DadosExtraidos


def build_graph(deps: Deps, checkpointer=None):
    """Constroi e compila o grafo. `deps` injeta extrator/OCR; `checkpointer` habilita retomada."""

    def _wrap(fn):
        def inner(state: AnalysisState) -> dict:
            return fn(state, deps)

        inner.__name__ = fn.__name__
        return inner

    g = StateGraph(AnalysisState)

    g.add_node("ingestao", _wrap(nodes.no_ingestao))
    g.add_node("ocr", _wrap(nodes.no_ocr))
    g.add_node("extracao", _wrap(nodes.no_extracao))
    g.add_node("validacao_confianca", _wrap(nodes.no_validacao_confianca))
    g.add_node("indicadores", _wrap(nodes.no_indicadores))
    g.add_node("inconsistencias", _wrap(nodes.no_inconsistencias))
    g.add_node("pre_parecer", _wrap(nodes.no_pre_parecer))
    g.add_node("revisao_humana", _wrap(nodes.no_revisao_humana))
    g.add_node("registro_auditoria", _wrap(nodes.no_registro_auditoria))

    g.add_edge(START, "ingestao")
    # e1 — roteamento por formato (OCR ou extracao direta)
    g.add_conditional_edges(
        "ingestao", nodes.roteia_ingestao,
        {"ocr": "ocr", "extracao": "extracao"},
    )
    g.add_edge("ocr", "extracao")
    g.add_edge("extracao", "validacao_confianca")
    # e2 — baixa confianca escala direto, sem calculo
    g.add_conditional_edges(
        "validacao_confianca", nodes.roteia_confianca,
        {"indicadores": "indicadores", "revisao_humana": "revisao_humana"},
    )
    g.add_edge("indicadores", "inconsistencias")
    g.add_edge("inconsistencias", "pre_parecer")
    g.add_edge("pre_parecer", "revisao_humana")
    # e3 — aprovado/devolvido (ambos consolidam auditoria)
    g.add_conditional_edges(
        "revisao_humana", nodes.roteia_revisao,
        {"aprovado": "registro_auditoria", "devolvido": "registro_auditoria"},
    )
    g.add_edge("registro_auditoria", END)

    return g.compile(checkpointer=checkpointer)


def build_demo_graph(dados: DadosExtraidos, checkpointer=None):
    """Grafo em modo demo: extrator mock + OCR no-op. Sem custo de API (RF-12)."""
    deps = Deps(extractor=MockExtractor(dados), ocr_engine=NoopOcrEngine())
    return build_graph(deps, checkpointer=checkpointer)


def build_real_graph(checkpointer=None, model: str | None = None, api_key: str | None = None):
    """Grafo em modo real: extrator Anthropic (Haiku) + OCR no-op. Requer chave/credito."""
    from .extraction.extractor import AnthropicExtractor  # lazy (langchain)

    deps = Deps(
        extractor=AnthropicExtractor(model=model, api_key=api_key),
        ocr_engine=NoopOcrEngine(),
    )
    return build_graph(deps, checkpointer=checkpointer)
