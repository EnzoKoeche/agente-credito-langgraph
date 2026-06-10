# Resultados das Evals (curado)

- **Data:** 2026-06-10
- **Versao prompt:** `p-1.0.0` · **Modelo:** `mock` (evals gratuitas, sem API)
- **Custo:** US$ 0,00 (extrator mock injetavel; nenhuma chamada paga).

## Evals deterministicas (gratuitas)

| Eval | Categoria | Resultado | Status |
|------|-----------|-----------|--------|
| EVAL-DET-01 | consistente | 24/24 | PASS |
| EVAL-DET-02 | media | 24/24 | PASS |
| EVAL-DET-03 | alta | 24/24 | PASS |
| EVAL-DET-04 | dado_ausente | 24/24 | PASS |
| EVAL-DET-05 | baixa_confianca | 25/25 | PASS |
| EVAL-DET-06 | simulacao | 24/24 | PASS |
| EVAL-DET-07 | bordas | 20/20 | PASS |

## Evals de grafo (gratuitas)

| Eval | Categoria | Resultado | Status |
|------|-----------|-----------|--------|
| EVAL-G2 | roteamento e1/e2/e3 | 17/17 | PASS |
| EVAL-G1 | retomada pos-interrupt (hash igual) | 1/1 | PASS |

## Caveats honestos

- **Gabarito derivado das regras** (oracle independente em `eval/oracle.py`). Para severidade e roteamento, o oracle re-enuncia a regra com literais proprios (pega divergencia real). Para a Tabela Price (EVAL-DET-06) e o limiar de confianca, oracle e producao coincidem por construcao -> a eval prova **regressao**, nao correcao independente.
- **Sem API:** estas evals nao exercitam o LLM real. Alucinacao/injecao/PII fim-a-fim (EVAL-PAGA-*) ficam para a Fase 2, com guard de custo.
- **EVAL-G1** valida a igualdade do estado serializado restaurado do checkpoint; nao prova ausencia de efeitos colaterais externos.
