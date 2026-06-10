"""Oracle independente das evals — o GABARITO.

Re-enuncia as regras de dominio com literais proprios, SEM importar a producao
(nem `agente_credito.config`). E' deliberadamente uma segunda implementacao: se a
producao e o oracle divergirem, a eval acusa. Caveat honesto: onde a regra e' uma
formula unica (ex.: Price), oracle e producao coincidem por construcao — nesse caso
a eval prova regressao (mudou a formula? quebrou?), nao correcao independente.
"""

from __future__ import annotations

# Literais do dominio (espelham docs/requisitos.md, escritos aqui de forma autonoma)
_MEDIA = 0.30
_ALTA = 0.50
_CONFIANCA = 0.60


def severidade_esperada(declarado, comprovado) -> str:
    """Severidade da inconsistencia (RF-04), comparacao estrita."""
    if declarado is None or comprovado is None or declarado <= 0:
        return "dado_ausente"
    d = round(abs(declarado - comprovado) / declarado, 10)
    if d > _ALTA:
        return "alta"
    if d > _MEDIA:
        return "media"
    return "consistente"


def parcela_esperada(valor, taxa_mensal, n_parcelas) -> float:
    """Parcela pela Tabela Price (RF-03)."""
    if taxa_mensal == 0:
        return valor / n_parcelas
    i = taxa_mensal
    return valor * i / (1 - (1 + i) ** (-n_parcelas))


def escalonamento_esperado(confianca) -> bool:
    """True se a extracao deve escalar direto para revisao humana (e2)."""
    return confianca is None or confianca < _CONFIANCA


def rota_e1_esperada(formato: str) -> str:
    return "ocr" if formato in ("imagem", "pdf_escaneado") else "extracao"


def rota_e2_esperada(confianca) -> str:
    return "revisao_humana" if escalonamento_esperado(confianca) else "indicadores"


def rota_e3_esperada(decisao: str) -> str:
    return "devolvido" if decisao == "devolvido" else "aprovado"
