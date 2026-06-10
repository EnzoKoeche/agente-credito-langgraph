"""TEST-GRAPH-ROUTE — roteadores das arestas condicionais e1/e2/e3 (RF-01/06, EVAL-G2)."""

from __future__ import annotations

from agente_credito.nodes import roteia_confianca, roteia_ingestao, roteia_revisao
from agente_credito.state import (
    AnalysisState,
    Decisao,
    DecisaoHumana,
    Documento,
    Formato,
)


def test_e1_imagem_ou_pdf_escaneado_vai_para_ocr():
    st = AnalysisState(
        documentos=[Documento(nome="rg.png", formato=Formato.IMAGEM, requer_ocr=True)]
    )
    assert roteia_ingestao(st) == "ocr"


def test_e1_txt_vai_direto_para_extracao():
    st = AnalysisState(
        documentos=[Documento(nome="ficha.txt", formato=Formato.TXT, requer_ocr=False)]
    )
    assert roteia_ingestao(st) == "extracao"


def test_e2_baixa_confianca_escala():
    assert roteia_confianca(AnalysisState(escalonado=True)) == "revisao_humana"
    assert roteia_confianca(AnalysisState(escalonado=False)) == "indicadores"


def test_e3_aprovado_e_devolvido():
    aprovado = AnalysisState(decisao_humana=DecisaoHumana(decisao=Decisao.APROVADO))
    devolvido = AnalysisState(decisao_humana=DecisaoHumana(decisao=Decisao.DEVOLVIDO))
    assert roteia_revisao(aprovado) == "aprovado"
    assert roteia_revisao(devolvido) == "devolvido"
