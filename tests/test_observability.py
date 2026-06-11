"""TEST-OBS — tracing opcional (Langfuse): no-op sem chaves, PII mascarada, grafo intacto.

Nenhum teste aqui toca a rede ou exige chaves Langfuse reais: o handler e'
injetavel e o caminho sem chaves devolve o config intocado.
"""

from __future__ import annotations

from langchain_core.callbacks import BaseCallbackHandler

from agente_credito import observability as obs
from agente_credito.graph import build_demo_graph
from agente_credito.persistence import sqlite_checkpointer
from agente_credito.state import AnalysisState, Documento, Formato


def _sem_chaves(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)


def test_sem_chaves_tracing_desligado_e_config_intacto(monkeypatch):
    _sem_chaves(monkeypatch)
    cfg = {"configurable": {"thread_id": "t-obs-1"}}
    assert obs.tracing_habilitado() is False
    assert obs.criar_handler() is None
    # devolve o MESMO objeto: nenhum custo, nenhuma chave nova no config
    assert obs.config_com_tracing(cfg, run_name="x") is cfg
    assert "callbacks" not in cfg and "metadata" not in cfg


def test_so_uma_chave_continua_desligado(monkeypatch):
    _sem_chaves(monkeypatch)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-x")
    assert obs.tracing_habilitado() is False


def test_handler_injetado_anexa_callbacks_run_name_e_metadata():
    cfg = {"configurable": {"thread_id": "t-obs-2"}}
    sentinela = object()
    novo = obs.config_com_tracing(
        cfg,
        run_name="run-teste",
        metadata={"langfuse_session_id": "sessao-1"},
        handler=sentinela,
    )
    assert novo is not cfg
    assert "callbacks" not in cfg  # original intocado
    assert sentinela in novo["callbacks"]
    assert novo["run_name"] == "run-teste"
    assert novo["configurable"]["thread_id"] == "t-obs-2"
    md = novo["metadata"]
    assert md["langfuse_session_id"] == "sessao-1"
    assert md["versao_prompt"] and md["versao_modelo"]
    assert "agente-credito-langgraph" in md["langfuse_tags"]


def test_mascaramento_recursivo_nao_vaza_pii():
    dado = {
        "texto": "Cliente CPF 123.456.789-00, contato maria@exemplo.com",
        "aninhado": {"tel": "(41) 99999-1234"},
        "lista": ["12345678900", 42],
        "tupla": ("ok", "x@y.com"),
        "numero": 7.5,
        "vazia": [],
    }
    m = obs._mascarar_recursivo(dado)
    plano = str(m)
    assert "123.456.789-00" not in plano
    assert "maria@exemplo.com" not in plano
    assert "99999-1234" not in plano
    assert "12345678900" not in plano
    assert "x@y.com" not in plano
    # estrutura e nao-strings preservadas
    assert m["numero"] == 7.5 and m["lista"][1] == 42
    assert isinstance(m["tupla"], tuple) and isinstance(m["vazia"], list)


def test_mask_aceita_assinatura_do_cliente_langfuse():
    """O cliente chama mask(data=...) por keyword (span.py do SDK)."""
    m = obs._mask_langfuse(data={"cpf": "123.456.789-00"})
    assert m["cpf"] == "***.***.***-**"
    assert obs._mask_langfuse(data=None) is None


def test_mascaramento_cobre_objetos_pydantic_crus(dados_consistentes):
    """O mask recebe o dado CRU (pre-serializacao): Pydantic com CPF nao pode vazar."""
    m = obs._mascarar_recursivo({"estado": dados_consistentes})
    plano = str(m)
    assert "123.456.789-00" not in plano
    assert isinstance(m["estado"], dict)  # virou dict mascarado


def test_tipo_desconhecido_vira_string_mascarada():
    class Opaco:
        def __str__(self):
            return "contato: fulano@x.com"

    assert "fulano@x.com" not in obs._mascarar_recursivo(Opaco())


def test_grafo_demo_roda_com_handler_e_emite_eventos(dados_consistentes):
    """Smoke: callbacks anexados via config nao quebram o grafo (ate o interrupt)."""

    class Contador(BaseCallbackHandler):
        def __init__(self):
            self.chains = 0

        def on_chain_start(self, *args, **kwargs):
            self.chains += 1

    contador = Contador()
    docs = [Documento(nome="ficha.txt", formato=Formato.TXT, conteudo="x")]
    cfg = obs.config_com_tracing(
        {"configurable": {"thread_id": "t-obs-3"}},
        run_name="teste-obs",
        handler=contador,
    )
    with sqlite_checkpointer(":memory:") as cp:
        app = build_demo_graph(dados_consistentes, checkpointer=cp)
        vistos = [k for ev in app.stream(AnalysisState(documentos=docs), cfg, stream_mode="updates") for k in ev]
    assert "pre_parecer" in vistos  # fluxo feliz chegou ate a revisao
    assert contador.chains > 0  # o handler recebeu eventos do grafo
