"""Smoke + fluxo HITL do front Streamlit, headless via AppTest (sem browser, sem API)."""

from __future__ import annotations

import pathlib

from streamlit.testing.v1 import AppTest

_APP = str(pathlib.Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


def _app():
    return AppTest.from_file(_APP, default_timeout=60).run()


def test_app_inicia_sem_erro():
    at = _app()
    assert not at.exception
    assert at.session_state.fase == "inicio"


def test_fluxo_aprovar():
    at = _app()
    at.selectbox(key="cenario").set_value("Aprovavel (consistente)")
    at.button(key="btn_rodar").click().run()
    assert not at.exception
    assert at.session_state.fase == "pausado"
    assert "indicadores" in at.session_state.progresso  # passou pelo calculo

    at.button(key="btn_aprovar").click().run()
    assert at.session_state.fase == "concluido"
    md = at.session_state.estado_final["metadados"]
    assert md["decisao"] == "aprovado"
    assert "111.222.333-44" not in md["resumo_mascarado"]  # PII mascarada


def test_fluxo_devolver_com_inconsistencia():
    at = _app()
    at.selectbox(key="cenario").set_value("Inconsistencia alta (renda)")
    at.button(key="btn_rodar").click().run()
    assert at.session_state.fase == "pausado"
    incs = at.session_state.estado_pausado["inconsistencias"]
    assert any(i["severidade"] == "alta" for i in incs)

    at.text_area(key="motivo").set_value("renda nao comprovada")
    at.button(key="btn_devolver").click().run()
    assert at.session_state.fase == "concluido"
    md = at.session_state.estado_final["metadados"]
    assert md["decisao"] == "devolvido"
    assert md["motivo_decisao"] == "renda nao comprovada"


def test_fluxo_baixa_confianca_escala_direto():
    at = _app()
    at.selectbox(key="cenario").set_value("Baixa confianca (escala direto)")
    at.button(key="btn_rodar").click().run()
    assert at.session_state.fase == "pausado"
    assert "indicadores" not in at.session_state.progresso  # escalou sem calcular
    assert at.session_state.estado_pausado["escalonado"] is True
