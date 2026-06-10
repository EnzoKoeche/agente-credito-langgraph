# PROGRESSO — agente-credito-langgraph

Reprojeto em LangGraph do [agente-bancario](https://github.com/EnzoKoeche/agente-bancario).
Espelha o log do Notion. Datas absolutas.

---

## 2026-06-10 — Fase 0: Engenharia de Requisitos

### O que foi feito
- **Decisões de escopo** coletadas (4 perguntas respondidas): repo em `/home/enzo/agente-credito-langgraph` (WSL/bash); escopo **Pessoa Física (PF)**; limiares **0,30/0,50 = discrepância relativa entre fontes** (`|declarado − comprovado| / declarado`); **OCR Tesseract local, pluggable**.
- **6 documentos** criados em `docs/`:
  - `visao.md` — visão e escopo (1 pág.), com o que entra e o que **explicitamente não entra**.
  - `requisitos.md` — **12 RFs** (MoSCoW + critérios Dado/Quando/Então) e **9 RNFs** com alvos numéricos, método de verificação e **caveat honesto**.
  - `casos_de_uso.md` — **5 UCs** com pré/pós-condições, fluxo principal, alternativos e exceção (EX-A PDF sem texto, EX-B baixa confiança, EX-C injeção, EX-D falha de API/retry).
  - `diagrama_casos_uso.md` — diagrama **Mermaid** (atores + `<<include>>`/`<<extend>>`) + legenda UC→nó.
  - `rastreabilidade.md` — matriz **RF ↔ UC ↔ nó do grafo ↔ eval ↔ teste pytest** (+ matriz RNF e cobertura das arestas), tudo em status "planejado".
  - `plano_eval.md` — eval determinística grátis (7 categorias, ~24 casos cada), paga com guard de custo (`--sanity`/`--full`), e eval de grafo (EVAL-G1 retomada, EVAL-G2 roteamento).
- **Auditoria adversarial de consistência cruzada** (agente dedicado): 5 achados (3 bloqueantes + 2 avisos), **todos corrigidos**. IDs, limiares e cross-refs 100% consistentes entre os 3 docs.

### Decisões tomadas
- **Topologia do grafo:** `n1 ingestao → n2 extracao → n3 validacao_confianca → n4 indicadores → n5 inconsistencias → n6 pre_parecer → n7 revisao_humana (interrupt) → n8 registro_auditoria`.
- **Arestas condicionais:** `e1` (PDF sem texto/imagem → OCR), `e2` (confiança < 0,6 → escalação direta sem cálculo), `e3` (aprovado/devolvido).
- **Regra RF-04 ancorada:** `> 0,50` ALTA · `0,30 < d ≤ 0,50` MÉDIA · `≤ 0,30` CONSISTENTE; bordas `0,30 → consistente`, `0,50 → média` (comparação **estrita**).
- **Sem `git init`/commit ainda:** Fase 0 é gate de revisão. A higiene de "commit zero" (`.gitignore` com `.env` + `.env.example` só placeholders) será o **primeiro passo da Fase 1**, após OK.

### Commits
- _(nenhum ainda — aguardando OK para `git init` no início da Fase 1)_

### Próximo passo
- Revisão dos 6 docs pelo Enzo → **OK explícito** → Fase 1 (esqueleto do grafo: estado tipado Pydantic, nós, arestas condicionais, `SqliteSaver`, `interrupt`).

---

## 2026-06-10 — Fase 1: Esqueleto do grafo

### O que foi feito
- **Ambiente:** venv com stack pinada em `requirements.txt` — `langgraph 1.2.4`, `langgraph-checkpoint-sqlite 3.1.0`, `langchain-anthropic 1.4.5`, `pydantic 2.13.4`, `pytest 9.0.3`. (Ambiente real tem Python 3.14; alvo documentado é 3.12 — caveat RNF-09.)
- **Pacote** `src/agente_credito/`: `state.py` (AnalysisState + submodelos Pydantic), `config.py` (limiares 0,30/0,50/0,6 + versão prompt/modelo), `tools/` (indicadores e inconsistências determinísticas), `security/` (PII + anti-injeção), `extraction/` (extrator injetável: Mock/Anthropic), `ocr/` (engine pluggable: Noop/Tesseract), `ingestion/` (detecção de formato), `deps.py`, `nodes.py` (9 nós + 3 roteadores), `graph.py` (montagem + `build_demo_graph`).
- **Grafo LangGraph:** nós n1..n8 + `ocr`; arestas condicionais e1 (OCR), e2 (baixa confiança → escalação), e3 (aprovado/devolvido); **interrupt** dinâmico na revisão humana; **SqliteSaver** retomável por `thread_id`; streaming `updates`.
- **Testes:** 51 passando; **cobertura das tools = 100%** (RNF-05). Inclui retomada com estado idêntico (RNF-06), roteamento e1/e2/e3, modo demo sem API, streaming, PII e anti-injeção.
- **Revisão adversarial** (workflow de 3 revisores + verificação): 14 achados, 10 confirmados. Corrigidos os 3 importantes (robustez de float na borda 0,30; mascaramento do motivo humano na auditoria; mascaramento de nome com fronteiras de palavra) + hardening (fail-safe em `roteia_revisao`, detecção de injeção/PII ampliada, cobertura do ramo OCR e ordem de streaming). 1 menor deferido e documentado (CPF cru no checkpoint — sem vazamento ativo).

### Decisões tomadas
- Escopo Fase 1 = núcleo do grafo + tools + testes. **Observabilidade (Langfuse), front Streamlit e as evals (`EVAL-*`) são Fase 2.**
- LLM e OCR **injetáveis** → modo demo roda o fluxo inteiro sem custo de API; os testes nunca tocam a API paga.
- `interrupt` dinâmico (`langgraph.types.interrupt` + `Command(resume=...)`) em vez de `interrupt_before`.

### Commits (locais — push é Fase 3, após secret-scan do histórico)
- `5ae07e2` chore: bootstrap do repo + docs da Fase 0
- `88243ea` feat(core): estado tipado, tools deterministicas e seguranca + testes
- `2f230cb` feat(grafo): LangGraph com arestas condicionais, interrupt HITL e checkpointing
- `e007569` fix(revisao): corrige achados da revisao adversarial da Fase 1

### Próximo passo
- Aguardando OK do Enzo para a **Fase 2** (Langfuse + streaming no front + Streamlit + implementar todas as evals do `plano_eval.md`).

---

## 2026-06-10 — Fase 2 (parcial): evals determinísticas grátis

### O que foi feito
- **Harness de eval** em `eval/`: `oracle.py` (gabarito independente das regras), `datasets_build.py` + datasets JSON versionados, `runner_det.py`/`runner_grafo.py` (exercitam o código de **produção**), `run_all.py` → `results/RESULTS.md` curado.
- **9 evals verdes, custo US$ 0,00** (extrator mock): `EVAL-DET-01..07` (consistente/média/alta/dado ausente/baixa confiança/simulação/bordas 0,30·0,50), `EVAL-G2` (roteamento e1/e2/e3, 17/17), `EVAL-G1` (retomada pós-interrupt, hash idêntico).
- Evals **integradas ao pytest** (`tests/test_evals.py`) → CI pega regressão de regra. Suite agora **60 testes**.
- **Fix de forward-compat:** `persistence.py` registra os tipos do estado no serde do checkpoint → elimina o aviso de "unregistered type" do LangGraph (que seria bloqueado em versões futuras).

### Decisões tomadas
- Entrada da Fase 2 = **evals grátis primeiro** (zero custo, fecha a coluna `EVAL-*` da rastreabilidade sem gastar). `EVAL-PAGA-*` (alucinação/injeção/PII fim-a-fim) ficam para depois, com guard de custo.
- Gabarito via **oracle independente** (re-enuncia a regra) para não ser circular; caveat honesto onde oracle e produção coincidem por construção (Price/confiança = prova de **regressão**, não de correção independente).

### Commits
- `e159fc9` feat(persistence): checkpointer com serde dos tipos do estado
- `291b969` feat(eval): harness de evals determinísticas gratuitas (EVAL-DET-01..07, G1, G2)

### Próximo passo
- Decidir continuação da Fase 2: front **Streamlit** (upload → progresso do grafo em tempo real → revisão HITL → auditoria), observabilidade **Langfuse**, e/ou **evals pagas** (com guard `--sanity` e custo estimado avisado antes).
