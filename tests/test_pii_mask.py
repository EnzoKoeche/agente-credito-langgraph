"""TEST-PII-MASK — mascaramento de PII em logs/auditoria (RF-11 / RNF-03)."""

from __future__ import annotations

from agente_credito.security.pii import contem_pii, mascarar_pii


def test_mascarar_cpf_formatado():
    out = mascarar_pii("CPF 123.456.789-00 do cliente")
    assert "123.456.789-00" not in out
    assert "***.***.***-**" in out


def test_mascarar_cpf_sem_pontuacao():
    out = mascarar_pii("cpf 12345678900 informado")
    assert "12345678900" not in out


def test_mascarar_email():
    out = mascarar_pii("contato joao@exemplo.com.br")
    assert "joao@exemplo.com.br" not in out
    assert "[EMAIL]" in out


def test_mascarar_nome():
    out = mascarar_pii("Cliente Joao da Silva aprovado", nome="Joao da Silva")
    assert "Joao da Silva" not in out
    assert "[NOME]" in out


def test_contem_pii():
    assert contem_pii("CPF 123.456.789-00")
    assert contem_pii("email a@b.com")
    assert not contem_pii("sem dado sensivel aqui")
    assert not contem_pii("")


def test_mascarar_none_vira_vazio():
    assert mascarar_pii(None) == ""


def test_nome_nao_faz_over_match():
    # 'Ana' nao pode mascarar 'ana' dentro de 'Mariana' (fronteira de palavra)
    assert mascarar_pii("Ana Paula e Mariana", nome="Ana") == "[NOME] Paula e Mariana"


def test_nome_com_espacos_multiplos_ainda_mascara():
    out = mascarar_pii("Cliente Joao  da  Silva aprovado", nome="Joao da Silva")
    assert "Joao" not in out
    assert "[NOME]" in out


def test_contem_pii_detecta_telefone():
    assert contem_pii("ligue 11 98765-4321")
