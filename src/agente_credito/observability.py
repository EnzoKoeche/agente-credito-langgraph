"""Observabilidade opcional via Langfuse — tracing por run.

Regras:
- SEM `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` no ambiente: tudo aqui e'
  no-op — o grafo roda exatamente como antes, sem dependencia de rede (os
  testes nunca exigem as chaves).
- COM as chaves: cada run vira um trace (nos do grafo, latencia por no,
  tokens/custo da chamada LLM) com versao de prompt/modelo como metadados e
  `thread_id` como sessao.
- PII NUNCA sai do processo em claro: o cliente Langfuse e' criado com `mask`
  ligado ao `security.pii.mascarar_pii` — mesmo invariante da trilha de
  auditoria (RF-11/RNF-03).

Import de `langfuse` e' lazy: a lib so carrega quando o tracing esta ligado.
"""

from __future__ import annotations

import os
from typing import Any

from .config import VERSAO_PROMPT, modelo_configurado
from .security.pii import mascarar_pii


def tracing_habilitado() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def _mascarar_recursivo(dado: Any) -> Any:
    """Mascara PII em qualquer estrutura ANTES de ela sair do processo.

    O Langfuse aplica o mask no dado CRU, antes da serializacao (span.py,
    `_process_media_and_apply_mask`) — entao objetos Pydantic (estado do grafo
    com CPF!) chegam aqui inteiros. Politica fail-closed: tipo que nao sabemos
    percorrer vira string mascarada; excecao vira marcador. Nunca levanta.
    """
    try:
        if dado is None or isinstance(dado, (bool, int, float)):
            return dado
        if isinstance(dado, str):
            return mascarar_pii(dado)
        if isinstance(dado, dict):
            return {k: _mascarar_recursivo(v) for k, v in dado.items()}
        if isinstance(dado, list):
            return [_mascarar_recursivo(v) for v in dado]
        if isinstance(dado, tuple):
            return tuple(_mascarar_recursivo(v) for v in dado)
        if hasattr(dado, "model_dump"):  # Pydantic -> dict mascarado
            return _mascarar_recursivo(dado.model_dump(mode="json"))
        return mascarar_pii(str(dado))  # desconhecido: fail-closed
    except Exception:
        return "[MASCARAMENTO_FALHOU]"


def _mask_langfuse(*, data: Any = None, **_: Any) -> Any:
    """Adaptador com a assinatura que o cliente Langfuse exige: `mask(data=...)`."""
    return _mascarar_recursivo(data)


def criar_handler():
    """CallbackHandler do Langfuse (com mask de PII no cliente); None sem chaves."""
    if not tracing_habilitado():
        return None
    from langfuse import Langfuse  # lazy
    from langfuse.langchain import CallbackHandler  # lazy

    # So o `mask` precisa vir por codigo; chaves e host o SDK resolve do ambiente
    # (LANGFUSE_PUBLIC_KEY/SECRET_KEY; LANGFUSE_BASE_URL -> LANGFUSE_HOST -> default).
    # O client e' singleton por public_key — chamadas repetidas sao idempotentes.
    Langfuse(mask=_mask_langfuse)
    return CallbackHandler()


def config_com_tracing(
    cfg: dict,
    *,
    run_name: str,
    metadata: dict | None = None,
    handler=None,
) -> dict:
    """Devolve o config do LangGraph com o tracing anexado; intacto sem tracing.

    `handler` e' injetavel para testes (qualquer callback handler serve). Sem
    handler e sem chaves no ambiente, devolve o MESMO objeto `cfg`, sem copia.
    """
    handler = handler if handler is not None else criar_handler()
    if handler is None:
        return cfg
    novo = dict(cfg)
    novo["callbacks"] = list(cfg.get("callbacks") or []) + [handler]
    novo["run_name"] = run_name
    novo["metadata"] = {
        **(cfg.get("metadata") or {}),
        "versao_prompt": VERSAO_PROMPT,
        "versao_modelo": modelo_configurado(),
        "langfuse_tags": ["agente-credito-langgraph"],
        **(metadata or {}),
    }
    return novo
