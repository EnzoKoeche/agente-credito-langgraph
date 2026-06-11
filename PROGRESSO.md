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

---

## 2026-06-10 — Fase 2 (parcial): front Streamlit

### O que foi feito
- **App Streamlit fino** (`app/streamlit_app.py` + `app/scenarios.py`): cenário/upload → **progresso do grafo em streaming** → **revisão humana (aprovar/devolver)** → **trilha de auditoria** (PII mascarada). Single-page, sem `st.rerun` (determinístico).
- **Modo demo** (3 cenários sintéticos: aprovável / inconsistência alta / baixa confiança) sem custo + **modo real** (Anthropic via `build_real_graph`, requer chave).
- Verificado **headless via AppTest** (4 fluxos: init, aprovar, devolver, baixa-confiança-escala) + **boot real** do servidor (`/_stcore/health` → ok). Suite agora **64 testes**.

### Decisões tomadas
- Front em **fluxo linear empilhado** (entrada → progresso → revisão → auditoria) em vez de `st.rerun`, para ser determinístico sob AppTest e ler como página única.
- Cenários sintéticos no demo (em vez de parsing de upload) para exibir os 3 caminhos do grafo sem LLM.

### Commits
- `fa4cf00` feat(front): app Streamlit fino (upload → progresso → revisão HITL → auditoria)

### Próximo passo
- Restam da Fase 2: **Langfuse** (tracing por run: versão de prompt, custo, latência) e **evals pagas** (`EVAL-PAGA-HALU/INJ/PII`, com guard `--sanity` e custo avisado). Depois, **Fase 3** (README final com comparativo SDK×LangGraph, secret-scan do histórico, push público via `gh`).

---

## 2026-06-10 — Fase 2 (evals pagas) + Fase 3 (parcial)

### O que foi feito
- **Evals pagas (harness):** `eval/run_paga.py` com **guard de custo** — dry-run por padrão (só estima, US$0,00), `--run` exigido para gastar, aborta sem `ANTHROPIC_API_KEY`. EVAL-PAGA-HALU/INJ/PII (datasets em `eval/datasets/paga/`), `cost.py` com preços do Haiku 4.5 (consultados na referência, não de memória). Estimativa `--sanity` ≈ US$0,02 (6 dossiês, dentro do RNF-01). Teste pago **pulado sem chave** (CI não gasta). **Não executado** (sem chave — por design de segurança). Commit `2cc0835`.
- **Notion:** página "Reprojeto LangGraph — agente-credito-langgraph" criada como filha de "🏦 Agente de Análise de Crédito — Estado do Projeto" (via MCP).
- **Fase 3 (parcial):** README enriquecido — **diagrama Mermaid do grafo**, seção de **resultados das evals** (com caveats) e a seção-centro **"SDK pura × LangGraph — trade-offs reais"** (checkpointing/interrupt/roteamento ganham; verbosidade/serde do checkpoint custam; custo/latência idênticos).

### Segurança
- **Chave de API vazada no chat** (3ª vez no projeto) — recusada, **não usada nem gravada**; orientado a rotacionar. Memória registrada. Scan do histórico do repo: **limpo** (só o placeholder do `.env.example`).

### Pendências (precisam do Enzo)
- Rotacionar a chave; depois `python eval/run_paga.py --sanity --run` com a chave nova no `.env`.
- **Push público:** sem rede para `github.com` deste WSL. Comando pronto: `gh repo create EnzoKoeche/agente-credito-langgraph --public --source=. --remote=origin --push`.

### Próximo passo
- Push público (Enzo) → colar link no Notion → opcional: Langfuse + screenshot da demo no README.

---

## 2026-06-10 — Checagem pós-push + decisão sobre a chave

### O que foi feito
- **Push público confirmado:** `main` no GitHub = `ae3d872` (12 commits), repo acessível sem autenticação. (`api.github.com` segue bloqueada no WSL — `gh` falha; `github.com` funciona via git.)
- **Secret-scan reconfirmado** em histórico completo + working tree + remoto: único match de `sk-ant-` é o placeholder do `.env.example`. `.env` nunca existiu no repo e está no `.gitignore`.
- **Dry-run das evals pagas reverificado:** 6 dossiês, ~US$ 0,021 total (~US$ 0,0035/dossiê — dentro do RNF-01). Nenhuma chamada paga.
- **Notion sincronizado:** pendências atualizadas (push concluído, rotação dispensada), Fase 3 marcada concluída, linha de sessão adicionada.

### Decisões tomadas
- **Rotação da chave dispensada (decisão do Enzo):** chave de teste pessoal, risco aceito. Restrição dura que permanece: a chave NUNCA entra no repo do GitHub (`.gitignore` + secret-scan antes de push).

### Pendências (precisam do Enzo)
- Criar `.env` (a partir do `.env.example`) com a `ANTHROPIC_API_KEY` — sem colar a chave em chat — e rodar `python eval/run_paga.py --sanity --run` (≈ US$ 0,02).

### Próximo passo
- Evals pagas `--sanity --run` → registrar custo real em `eval/results/RESULTS.md` → opcional: Langfuse, screenshot da demo no README, deploy no Streamlit Community Cloud.

---

## 2026-06-10 — Evals pagas executadas (6/6 PASS) + fix do extrator

### O que foi feito
- **Fix bloqueante:** `runner_paga` chama `build_real_graph` sem `api_key` e o `AnthropicExtractor` repassava `api_key=None` explícito ao `ChatAnthropic` — o que desliga o fallback do env e quebrava com `ValidationError` **antes** de qualquer chamada paga (US$ 0,00 gasto no erro). Corrigido em `extraction/extractor.py`: `api_key` só é passado quando definido.
- **Evals pagas `--sanity --run`:** EVAL-PAGA-HALU 2/2 · EVAL-PAGA-INJ 2/2 · EVAL-PAGA-PII 2/2 — **6/6 PASS**. Custo ~US$ 0,021 estimado (o harness não agrega o usage real). `RESULTS.md` ganhou a seção das pagas + caveats.
- **Suite revalidada:** 64 testes verdes (rodada com `--deselect tests/test_evals_paga.py::test_paga_sanity` para não gastar de novo).

### Alerta (resolvido na sequência)
- Com a chave no `.env`, **`pytest` completo executava o teste pago** (~US$ 0,02 por run) — o `skipif` era só "sem chave". Resolvido: o teste agora é **opt-in explícito** (`RUN_EVAL_PAGA=1` além da chave), com a flag documentada no `.env.example`. Verificado: suite completa com chave presente → 64 verdes + 1 skipped, US$ 0,00.

### Próximo passo
- Opcional: Langfuse (tracing), screenshot da demo no README, deploy no Streamlit Community Cloud.

---

## 2026-06-10 — Deploy público no Streamlit Community Cloud

### O que foi feito
- **Demo ao vivo:** [agente-credito-langgraph.streamlit.app](https://agente-credito-langgraph.streamlit.app) — deploy via share.streamlit.io (repo público, branch `main`, entrypoint `app/streamlit_app.py`, Python 3.12, **sem secrets**).
- A primeira tentativa de deploy não persistiu (workspace sem app → not_found para todos); a segunda, com o campo **App URL** preenchido, subiu na URL limpa. Verificado de fora com sessão anônima.
- **Segurança do custo:** o modo demo roda sem API; no modo real a chave é digitada na sidebar pelo próprio visitante — a chave do Enzo não existe no deploy.
- README ganhou link + badge "Demo ao vivo".

### Próximo passo
- Opcional: Langfuse (tracing) e screenshot da demo no README.

---

## 2026-06-11 — Observabilidade: Langfuse opcional com mask de PII

### O que foi feito
- **`src/agente_credito/observability.py`:** tracing por run via Langfuse — nós do grafo, latência, tokens/custo do LLM, versão de prompt/modelo como metadados, `thread_id` como sessão. **No-op sem as chaves** (`LANGFUSE_PUBLIC_KEY/SECRET_KEY`): sem rede, config devolvido intacto, import lazy.
- **PII nunca sai do processo:** cliente criado com `mask` fail-closed reusando `security/pii.mascarar_pii` — Pydantic vira dict mascarado, tipo desconhecido vira string mascarada, exceção vira marcador.
- **Fiação:** `app/streamlit_app.py` (`_rodar`/`_decidir`, sessão = thread_id) e `eval/runner_paga.py` (`eval-<caso>`). Deps pinadas: `langfuse 4.7.1` + `langchain 1.3.7` (exigido pela integração). README ganhou seção "Observabilidade (Langfuse)"; `.env.example` documentado.
- **Revisão contra o SDK instalado pegou 2 bugs antes do commit:** (1) o cliente chama `mask(data=...)` por keyword — assinatura posicional daria TypeError e traces 100% mascarados; (2) o mask recebe o dado **cru, pré-serialização** (`span.py`), então objetos Pydantic com CPF passariam inalterados — corrigido com o masker fail-closed. Verificado também: `langfuse_session_id`/`langfuse_tags` honrados e flush via `atexit` (evals curtas não perdem traces).
- **Suite: 72 verdes + 1 skipped (opt-in pago)** — 8 testes novos de observabilidade. Boot do Streamlit limpo com a fiação.

### Caveat honesto
- Tracing fim-a-fim com chaves reais não foi exercitado (sem conta Langfuse configurada); o que está verificado é o contrato com o SDK (assinatura/fluxo do mask, metadata, atexit) + no-op sem chaves.

### Próximo passo
- Opcional: criar projeto no cloud.langfuse.com, preencher as chaves no `.env` e olhar um trace real; screenshot da demo no README.

---

## 2026-06-11 — Langfuse verificado fim-a-fim (skill oficial + chaves reais)

### O que foi feito
- **Skill oficial instalada** (`npx skills add langfuse/skills` → `.agents/skills/langfuse`, gitignorada) e seguida: docs-first, auditoria de baseline (handler de framework, nomes descritivos, session_id, PII mascarada, flush — já cobertos).
- **Ajustes de best practice que a auditoria pegou:** (1) o código passava `host=` explícito lendo só `LANGFUSE_HOST` — atropelava a resolução do SDK e mandaria traces pro host errado com `LANGFUSE_BASE_URL` (nome oficial atual; projeto do Enzo é US). Agora só o `mask` vai por código e o SDK resolve chaves/host do ambiente. (2) o front Streamlit não carregava o `.env` → `load_dotenv()` adicionado. (3) `langfuse_user_id` = revisor na decisão HITL (app user-aware).
- **Verificação E2E com chaves reais (projeto US):** grafo demo (US$ 0,00 de LLM) com tracing → flush → `GET /api/public/traces`: 2 traces na sessão (execução + decisão), tag e `versao_prompt` presentes, **CPF cru ausente do payload e máscara `***.***.***-**` presente** — invariante de PII confirmado contra o serviço real.
- Suite: 72 verdes + 1 skipped.

### Próximo passo
- Opcional: screenshot da demo no README. Projeto sem furos vs. objetivo declarado.
