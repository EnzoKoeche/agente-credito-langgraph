"""Estado tipado do grafo (`AnalysisState`) e seus submodelos Pydantic.

Cada no escreve campos distintos do estado; o LangGraph mescla os updates
(dict parcial) sobre este modelo. Campos de trabalho (timestamps, contadores,
trilha) sao consolidados em `MetadadosAuditoria` no no `registro_auditoria`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums de dominio
# ---------------------------------------------------------------------------
class Formato(str, Enum):
    TXT = "txt"
    PDF_TEXTO = "pdf_texto"
    PDF_ESCANEADO = "pdf_escaneado"
    IMAGEM = "imagem"


class Severidade(str, Enum):
    CONSISTENTE = "consistente"
    MEDIA = "media"
    ALTA = "alta"
    DADO_AUSENTE = "dado_ausente"


class Decisao(str, Enum):
    APROVADO = "aprovado"
    DEVOLVIDO = "devolvido"


# ---------------------------------------------------------------------------
# Submodelos
# ---------------------------------------------------------------------------
class Documento(BaseModel):
    """Documento bruto do dossie."""

    nome: str
    formato: Formato
    conteudo: str = ""          # texto bruto (preenchido por OCR quando aplicavel)
    requer_ocr: bool = False


class ParConferencia(BaseModel):
    """Par (declarado, comprovado) de uma mesma grandeza, vindo de fontes distintas."""

    campo: str
    valor_declarado: float | None = None
    valor_comprovado: float | None = None
    fonte_declarado: str = ""
    fonte_comprovado: str = ""


class DadosExtraidos(BaseModel):
    """Saida estruturada da extracao (RF-02), validada por schema."""

    renda_liquida_mensal: float | None = None
    despesas_fixas_mensais: float | None = None
    soma_parcelas_mensais: float | None = None
    valor_credito_solicitado: float | None = None
    taxa_mensal: float | None = None
    n_parcelas: int | None = None
    pares_para_conferencia: list[ParConferencia] = Field(default_factory=list)
    # PII — sempre mascarada em logs/auditoria (RF-11)
    nome_cliente: str | None = None
    cpf: str | None = None
    # Confianca atribuida pelo extrator (0..1)
    confianca: float = 1.0


class Indicadores(BaseModel):
    """Indicadores calculados por tools deterministicas (RF-03)."""

    comprometimento_de_renda: float | None = None
    capacidade_de_pagamento: float | None = None
    parcela_simulada: float | None = None


class Inconsistencia(BaseModel):
    """Discrepancia entre fontes classificada por severidade (RF-04)."""

    campo: str
    valor_declarado: float | None = None
    valor_comprovado: float | None = None
    discrepancia: float | None = None
    severidade: Severidade
    fontes: list[str] = Field(default_factory=list)


class PreParecer(BaseModel):
    """Rascunho assistivo do pre-parecer (RF-05) — sem veredito de aprovacao."""

    texto: str
    fontes_citadas: list[str] = Field(default_factory=list)


class DecisaoHumana(BaseModel):
    """Decisao do analista capturada no `interrupt` (RF-06)."""

    decisao: Decisao
    motivo: str = ""
    revisor: str = ""


class MetadadosAuditoria(BaseModel):
    """Trilha de auditoria (RF-07) — PII ja mascarada."""

    versao_prompt: str
    versao_modelo: str
    custo_usd: float = 0.0
    timestamp_inicio: str | None = None
    timestamp_fim: str | None = None
    resumo_mascarado: str = ""
    escalonado_baixa_confianca: bool = False
    tentativas_injecao: int = 0
    decisao: Decisao | None = None
    motivo_decisao: str = ""


# ---------------------------------------------------------------------------
# Estado do grafo
# ---------------------------------------------------------------------------
class AnalysisState(BaseModel):
    """Estado tipado compartilhado por todos os nos do grafo."""

    # Entrada
    documentos: list[Documento] = Field(default_factory=list)

    # Resultados de cada etapa
    dados_extraidos: DadosExtraidos | None = None
    confianca_extracao: float | None = None
    indicadores: Indicadores | None = None
    inconsistencias: list[Inconsistencia] = Field(default_factory=list)
    rascunho_pre_parecer: PreParecer | None = None
    decisao_humana: DecisaoHumana | None = None
    metadados: MetadadosAuditoria | None = None

    # Campos de trabalho (consolidados em metadados no registro_auditoria)
    inicio_ts: str | None = None
    escalonado: bool = False
    tentativas_injecao: int = 0
    custo_usd: float = 0.0
    trilha: list[str] = Field(default_factory=list)
    erros: list[str] = Field(default_factory=list)
