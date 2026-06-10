"""Checkpointer SQLite com serde dos tipos do estado registrado (RF-08).

O LangGraph serializa o estado via msgpack e, ao reabrir um checkpoint persistido,
avisa sobre tipos "nao registrados" (e os bloqueara em versoes futuras). Aqui
registramos explicitamente os modelos de `state` na allowlist, tornando a retomada
limpa e a prova de futuro.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from . import state as _state

_MODULO = _state.__name__  # "agente_credito.state"
_ALLOW = {
    (_MODULO, nome)
    for nome in dir(_state)
    if isinstance(getattr(_state, nome), type)
    and getattr(_state, nome).__module__ == _MODULO
}

#: Serializer que permite desserializar os modelos do estado sem aviso/bloqueio.
STATE_SERDE = JsonPlusSerializer(allowed_msgpack_modules=_ALLOW)


@contextmanager
def sqlite_checkpointer(conn_string: str) -> Iterator[SqliteSaver]:
    """SqliteSaver retomavel por thread_id, com o serde do estado ja configurado.

    Uso:
        with sqlite_checkpointer("checkpoints.sqlite") as cp:
            app = build_graph(deps, checkpointer=cp)
    """
    with SqliteSaver.from_conn_string(conn_string) as saver:
        saver.serde = STATE_SERDE
        yield saver
