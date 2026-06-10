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
