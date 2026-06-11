# Resultados das Evals (curado)

- **Data:** 2026-06-10
- **Versao prompt:** `p-1.0.0`
- **Gratuitas:** extrator `mock`, US$ 0,00 · **Pagas:** `claude-haiku-4-5-20251001` (`--sanity --run`), ~US$ 0,021 estimado.

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

## Evals pagas (LLM real — Haiku) — executadas em 2026-06-10

| Eval | O que mede | Resultado | Status |
|------|-----------|-----------|--------|
| EVAL-PAGA-HALU | extracao fiel ao documento (sem invencao/omissao/divergencia) | 2/2 | PASS |
| EVAL-PAGA-INJ | injecao no documento nao corrompe a extracao (criterio duro estrutural) | 2/2 | PASS |
| EVAL-PAGA-PII | CPF/PII nao vazam no resumo mascarado nem no motivo da decisao | 2/2 | PASS |

- **Modo:** `--sanity --run` (2 casos por categoria, 6 dossies; 1 chamada Haiku por dossie).
- **Custo:** ~US$ 0,021 total (~US$ 0,0035/dossie — dentro do RNF-01 de <= US$ 0,01/dossie). Valor ESTIMADO: o harness nao agrega o usage real das respostas.

## Caveats honestos

- **Gabarito derivado das regras** (oracle independente em `eval/oracle.py`). Para severidade e roteamento, o oracle re-enuncia a regra com literais proprios (pega divergencia real). Para a Tabela Price (EVAL-DET-06) e o limiar de confianca, oracle e producao coincidem por construcao -> a eval prova **regressao**, nao correcao independente.
- **Escopo das gratuitas:** nao exercitam o LLM real — esse papel e das EVAL-PAGA-* acima.
- **Pagas em `--sanity`:** 2 casos por categoria, documentos sinteticos limpos — piso de sanidade, nao prova exaustiva (`--full` cobre todos os casos).
- **Fix necessario para rodar as pagas:** o runner nao passa `api_key` e o extrator repassava `None` explicito ao `ChatAnthropic`, desligando o fallback do env (quebrava antes de gastar). Corrigido em `extraction/extractor.py` (so passa `api_key` quando definido).
- **EVAL-G1** valida a igualdade do estado serializado restaurado do checkpoint; nao prova ausencia de efeitos colaterais externos.
