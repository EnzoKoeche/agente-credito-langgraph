"""Front Streamlit fino do agente-credito-langgraph.

Fluxo: cenario/upload -> progresso do grafo (streaming) -> revisao humana (HITL) -> auditoria.
Modo demo (extrator mock, sem custo) + modo real (Anthropic, requer chave).

Execucao:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import io
import pathlib
import sys
import tempfile
import uuid

_RAIZ = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(_RAIZ / "src"), str(_RAIZ / "app")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from langgraph.types import Command

import scenarios
from agente_credito.graph import build_demo_graph, build_real_graph
from agente_credito.persistence import sqlite_checkpointer
from agente_credito.state import AnalysisState, DadosExtraidos, Documento, Formato

st.set_page_config(page_title="Agente de Credito (LangGraph)", page_icon="🧭", layout="wide")

_CAMPOS_AUDIT = (
    "decisao",
    "motivo_decisao",
    "versao_prompt",
    "versao_modelo",
    "timestamp_inicio",
    "timestamp_fim",
    "tentativas_injecao",
    "escalonado_baixa_confianca",
)


# --------------------------------------------------------------------------- #
# Estado da sessao                                                            #
# --------------------------------------------------------------------------- #
def _init() -> None:
    if "fase" not in st.session_state:
        fd, db = tempfile.mkstemp(suffix=".sqlite")
        import os

        os.close(fd)
        st.session_state.fase = "inicio"
        st.session_state.db = db
        st.session_state.progresso = []
        st.session_state.estado_pausado = None
        st.session_state.estado_final = None


def _construir_app(cp):
    if st.session_state.get("modo") == "real":
        return build_real_graph(
            checkpointer=cp,
            model=st.session_state.get("modelo") or None,
            api_key=st.session_state.get("api_key") or None,
        )
    dados = DadosExtraidos(**st.session_state.dados)
    return build_demo_graph(dados, checkpointer=cp)


def _docs_de_uploads(uploads) -> list[Documento]:
    docs = []
    for uf in uploads or []:
        nome = uf.name
        low = nome.lower()
        if low.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(uf.getvalue()))
            texto = "\n".join((p.extract_text() or "") for p in reader.pages)
            fmt = Formato.PDF_TEXTO if texto.strip() else Formato.PDF_ESCANEADO
            docs.append(Documento(nome=nome, formato=fmt, conteudo=texto))
        elif low.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            docs.append(Documento(nome=nome, formato=Formato.IMAGEM, conteudo=""))
        else:
            docs.append(
                Documento(
                    nome=nome,
                    formato=Formato.TXT,
                    conteudo=uf.getvalue().decode("utf-8", errors="replace"),
                )
            )
    return docs


def _rodar() -> None:
    if st.session_state.get("modo") == "real":
        docs = _docs_de_uploads(st.session_state.get("uploads"))
        if not docs:
            st.warning("Envie ao menos um documento para o modo real.")
            return
        st.session_state.dados = None
    else:
        cenario = st.session_state.get("cenario") or next(iter(scenarios.CENARIOS))
        dados, docs = scenarios.CENARIOS[cenario]()
        st.session_state.dados = dados.model_dump(mode="json")

    tid = uuid.uuid4().hex
    st.session_state.thread_id = tid
    st.session_state.docs = [d.model_dump(mode="json") for d in docs]
    st.session_state.progresso = []
    cfg = {"configurable": {"thread_id": tid}}

    with sqlite_checkpointer(st.session_state.db) as cp:
        app = _construir_app(cp)
        with st.status("Executando o grafo...", expanded=True) as status:
            for ev in app.stream(AnalysisState(documentos=docs), cfg, stream_mode="updates"):
                if "__interrupt__" in ev:
                    status.write("⏸️ interrupt — aguardando revisao humana")
                    continue
                for node in ev:
                    st.session_state.progresso.append(node)
                    status.write(f"✓ {node}")
            status.update(label="Grafo pausado na revisao humana", state="complete")
        snap = app.get_state(cfg)
    st.session_state.estado_pausado = AnalysisState(**snap.values).model_dump(mode="json")
    st.session_state.fase = "pausado"


def _decidir(decisao: str) -> None:
    cfg = {"configurable": {"thread_id": st.session_state.thread_id}}
    with sqlite_checkpointer(st.session_state.db) as cp:
        app = _construir_app(cp)
        final = app.invoke(
            Command(
                resume={
                    "decisao": decisao,
                    "motivo": st.session_state.get("motivo", ""),
                    "revisor": st.session_state.get("revisor", ""),
                }
            ),
            cfg,
        )
    st.session_state.estado_final = AnalysisState(**final).model_dump(mode="json")
    st.session_state.fase = "concluido"


# --------------------------------------------------------------------------- #
# Render                                                                      #
# --------------------------------------------------------------------------- #
def _sidebar() -> None:
    st.sidebar.title("🧭 Agente de Credito")
    st.sidebar.caption("Apoio ao analista — o agente NUNCA decide (HITL).")
    st.sidebar.radio("Modo", ["demo", "real"], key="modo", help="demo: sem custo de API.")
    if st.session_state.get("modo") == "real":
        st.sidebar.text_input("ANTHROPIC_API_KEY", type="password", key="api_key")
        st.sidebar.text_input("Modelo", value="claude-haiku-4-5-20251001", key="modelo")
    if st.sidebar.button("Nova analise", key="btn_nova"):
        for k in ("thread_id", "dados", "docs", "estado_pausado", "estado_final"):
            st.session_state.pop(k, None)
        st.session_state.progresso = []
        st.session_state.fase = "inicio"


def _secao_entrada() -> None:
    st.subheader("1. Dossie")
    if st.session_state.get("modo") == "real":
        st.file_uploader(
            "Documentos (txt/PDF/imagem)",
            type=["txt", "pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="uploads",
        )
    else:
        st.selectbox("Cenario de demonstracao", list(scenarios.CENARIOS), key="cenario")
    if st.button("▶ Rodar analise", key="btn_rodar", type="primary"):
        _rodar()


def _secao_progresso() -> None:
    st.subheader("2. Progresso do grafo")
    st.write(" → ".join(st.session_state.progresso) or "(sem eventos)")


def _secao_revisao() -> None:
    est = st.session_state.estado_pausado
    st.subheader("3. Revisao humana (HITL)")
    if est.get("escalonado"):
        st.warning("Extracao com baixa confianca — escalado direto para revisao, SEM calculo.")
    indic = est.get("indicadores") or {}
    c1, c2, c3 = st.columns(3)
    c1.metric("Comprometimento", _pct(indic.get("comprometimento_de_renda")))
    c2.metric("Capacidade (R$)", _num(indic.get("capacidade_de_pagamento")))
    c3.metric("Parcela (R$)", _num(indic.get("parcela_simulada")))
    for inc in est.get("inconsistencias") or []:
        st.error(f"Inconsistencia [{inc['severidade']}] em '{inc['campo']}' "
                 f"(fontes: {', '.join(inc.get('fontes') or []) or 'n/d'})")
    pp = est.get("rascunho_pre_parecer")
    if pp:
        st.markdown("**Pre-parecer (PII mascarada, sem veredito):**")
        st.code(pp["texto"])
    st.text_area("Motivo (opcional)", key="motivo")
    st.text_input("Revisor", key="revisor")
    col_a, col_d = st.columns(2)
    if col_a.button("✅ Aprovar", key="btn_aprovar"):
        _decidir("aprovado")
    if col_d.button("↩️ Devolver", key="btn_devolver"):
        _decidir("devolvido")


def _secao_auditoria() -> None:
    md = st.session_state.estado_final["metadados"]
    st.subheader("4. Trilha de auditoria")
    if md["decisao"] == "aprovado":
        st.success(f"Decisao do analista: APROVADO")
    else:
        st.info(f"Decisao do analista: DEVOLVIDO")
    st.json({k: md.get(k) for k in _CAMPOS_AUDIT})
    st.markdown("**Resumo (PII mascarada):**")
    st.code(md.get("resumo_mascarado") or "(vazio)")


def _pct(v):
    return f"{v:.1%}" if isinstance(v, (int, float)) else "—"


def _num(v):
    return f"{v:,.2f}" if isinstance(v, (int, float)) else "—"


# --------------------------------------------------------------------------- #
# App                                                                         #
# --------------------------------------------------------------------------- #
_init()
_sidebar()
st.title("Analise de credito assistida por LangGraph")

_secao_entrada()
if st.session_state.fase in ("pausado", "concluido"):
    _secao_progresso()
if st.session_state.fase == "pausado":
    _secao_revisao()
if st.session_state.fase == "concluido":
    _secao_auditoria()
