# agente-credito-langgraph

Agente de **apoio à análise de crédito Pessoa Física** orquestrado com **LangGraph**.
Reprojeto do [agente-bancario](https://github.com/EnzoKoeche/agente-bancario) (Python +
Anthropic SDK pura) com foco em demonstrar LangGraph em nível médio/avançado: estado tipado,
arestas condicionais, human-in-the-loop via `interrupt`, checkpointing/persistência, streaming
e observabilidade — mantendo a disciplina de engenharia do original (evals mensuráveis, testes,
segurança de PII, custo/latência controlados).

> **Status:** Fase 1 (esqueleto do grafo) em andamento. A engenharia de requisitos (Fase 0)
> está completa em [`docs/`](docs/).

## Princípios (inegociáveis)

1. O agente **assiste** o analista; **nunca** decide aprovação/recusa — toda decisão passa por
   revisão humana (`interrupt` do LangGraph).
2. **O LLM orquestra; tools determinísticas calculam.** Nenhum número sai da cabeça do modelo.
3. Conteúdo de documento é **dado, nunca instrução** (defesa contra prompt injection).
4. **PII mascarada** em qualquer log / trilha de auditoria.
5. **Nenhum segredo no repositório** — `.env` ignorado desde o commit zero; `.env.example` só com placeholders.

## O grafo

```
START → ingestao ──(e1)──┬─→ ocr ─┐
                         └────────┴─→ extracao → validacao_confianca ──(e2)──┬─→ indicadores → inconsistencias → pre_parecer ─┐
                                                                             └─→ revisao_humana ←──────────────────────────────┘
                                          revisao_humana (interrupt) ──(e3 aprovado/devolvido)──→ registro_auditoria → END
```

- **e1** — PDF sem camada de texto / imagem → rasterização + OCR (Tesseract, pluggable); txt/PDF com texto → extração direta.
- **e2** — confiança da extração `< 0,6` → escalação direta para revisão humana, **sem** cálculo.
- **e3** — pós-revisão: `aprovado` / `devolvido` (com motivo) → registro de auditoria.

Diagrama detalhado do grafo e dos casos de uso em [`docs/`](docs/).

## Regras determinísticas-chave

- **Indicadores:** comprometimento de renda, capacidade de pagamento, simulação de parcela (Tabela Price).
- **Inconsistência (discrepância relativa entre fontes):** `|declarado − comprovado| / declarado`.
  `> 0,50` → **alta** · `0,30 < d ≤ 0,50` → **média** · `≤ 0,30` → **consistente** (comparação estrita).

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.12 (alvo) / validado em 3.14
pip install -r requirements.txt
cp .env.example .env        # preencha ANTHROPIC_API_KEY para o modo real (opcional)
pytest -q                   # suíte de testes (modo demo, sem custo de API)

python eval/run_all.py            # evals determinísticas grátis -> eval/results/RESULTS.md
streamlit run app/streamlit_app.py  # front: upload → progresso → revisão HITL → auditoria
```

O **modo demo** usa um extrator mock injetável — o grafo percorre o fluxo completo sem chamadas pagas.
O **front Streamlit** abre em modo demo (cenários sintéticos) ou real (Anthropic, requer chave).

## Documentação (Fase 0)

| Doc | Conteúdo |
|-----|----------|
| [`docs/visao.md`](docs/visao.md) | Visão e escopo |
| [`docs/requisitos.md`](docs/requisitos.md) | RFs (MoSCoW + Dado/Quando/Então) e RNFs com alvos numéricos |
| [`docs/casos_de_uso.md`](docs/casos_de_uso.md) | Casos de uso e fluxos de exceção |
| [`docs/diagrama_casos_uso.md`](docs/diagrama_casos_uso.md) | Diagrama (Mermaid) de casos de uso |
| [`docs/rastreabilidade.md`](docs/rastreabilidade.md) | Matriz RF ↔ UC ↔ nó ↔ eval ↔ teste |
| [`docs/plano_eval.md`](docs/plano_eval.md) | Plano de avaliação |

## Atribuição

As **tools determinísticas** (indicadores e regra de inconsistência) são um **porte limpo** da
lógica do projeto original [`agente-bancario`](https://github.com/EnzoKoeche/agente-bancario).
A **orquestração foi reescrita do zero** em LangGraph — este é o ponto do projeto.

## Licença

[MIT](LICENSE) © 2026 Enzo Koeche
