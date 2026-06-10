"""TEST-DEMO-MODE — fluxo completo em modo demo, sem custo de API (RF-12).

Exercita o caminho feliz inteiro: interrupt na revisao humana + retomada com
Command(resume=...), checando indicadores, pre-parecer, auditoria e PII mascarada.
"""

from __future__ import annotations

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from agente_credito.graph import build_demo_graph
from agente_credito.state import AnalysisState, Documento, Formato


def test_demo_fluxo_completo(dados_consistentes):
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="dados do cliente")]
    cfg = {"configurable": {"thread_id": "demo-1"}}
    with SqliteSaver.from_conn_string(":memory:") as cp:
        app = build_demo_graph(dados_consistentes, checkpointer=cp)
        r1 = app.invoke(AnalysisState(documentos=docs), cfg)
        assert "__interrupt__" in r1  # pausou na revisao humana (HITL)
        final = app.invoke(
            Command(resume={"decisao": "aprovado", "motivo": "ok", "revisor": "ana"}),
            cfg,
        )

    estado = AnalysisState(**final)
    # indicadores calculados pelas tools
    assert estado.indicadores is not None
    assert estado.indicadores.comprometimento_de_renda == 0.30
    assert estado.indicadores.parcela_simulada is not None
    # pre-parecer com fontes citadas, sem veredito embutido
    assert estado.rascunho_pre_parecer is not None
    assert estado.rascunho_pre_parecer.fontes_citadas
    # auditoria consolidada
    assert estado.metadados is not None
    assert estado.metadados.decisao.value == "aprovado"
    assert estado.metadados.versao_modelo  # registrada
    assert estado.trilha[-1] == "registro_auditoria"
    # PII mascarada na trilha (RF-11)
    assert "123.456.789-00" not in estado.metadados.resumo_mascarado
    assert "Joao da Silva" not in estado.metadados.resumo_mascarado


def test_demo_devolvido(dados_consistentes):
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="x")]
    cfg = {"configurable": {"thread_id": "demo-dev"}}
    with SqliteSaver.from_conn_string(":memory:") as cp:
        app = build_demo_graph(dados_consistentes, checkpointer=cp)
        app.invoke(AnalysisState(documentos=docs), cfg)
        final = app.invoke(
            Command(resume={"decisao": "devolvido", "motivo": "faltou comprovante", "revisor": "ana"}),
            cfg,
        )
    estado = AnalysisState(**final)
    assert estado.metadados.decisao.value == "devolvido"
    assert estado.metadados.motivo_decisao == "faltou comprovante"
