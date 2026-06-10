# Visao e Escopo

## 1. Contexto e problema

A analise de credito para Pessoa Fisica (PF) — credito pessoal e consignado — depende hoje de leitura manual de dossies heterogeneos (contracheques, comprovantes de renda, extratos), conferencia cruzada de valores declarados contra comprovados e calculo de indicadores feitos a mao ou em planilhas. Esse trabalho e lento, propenso a erro aritmetico, dificil de auditar e nao escala com o volume de propostas. O gargalo nao esta no julgamento — que e responsabilidade e competencia do analista — mas na preparacao do material para o julgamento: extrair, calcular, cruzar fontes e redigir um pre-parecer rastreavel. Por isso o agente ASSISTE o analista, automatizando a parte mecanica e mantendo a decisao com o humano.

## 2. Objetivo do projeto

Construir um agente em LangGraph que recebe o dossie de um cliente PF, extrai dados de forma estruturada e validada, calcula indicadores por tools deterministicas, detecta inconsistencias entre fontes e redige um pre-parecer com fontes citadas — pausando obrigatoriamente para revisao humana (HITL) antes de qualquer encaminhamento. A proposta de valor e dupla: reduzir drasticamente o tempo de preparacao de cada dossie e elevar a qualidade da decisao, entregando ao analista um pre-parecer consistente, calculado por codigo (nunca pelo modelo) e totalmente auditavel, sem nunca substituir o julgamento humano.

## 3. Publico-alvo

- **Analista de Credito** (ator primario): submete o dossie, revisa o pre-parecer e aprova ou devolve com motivo. E quem decide.
- **Gestor de Risco** (ator secundario): consulta a trilha de auditoria e define limiares e politicas de risco.

## 4. Em escopo (o que o agente FAZ)

- Ingestao multi-formato: txt, PDF com texto, PDF escaneado e imagem, com OCR sob demanda (RF-01).
- Extracao estruturada validada por schema Pydantic, com avaliacao de confianca (RF-02).
- Indicadores via tools deterministicas: comprometimento de renda, capacidade de pagamento e simulacao de parcela (Tabela Price) (RF-03).
- Deteccao de inconsistencias por discrepancia relativa entre fontes, com limiares 0,30/0,50 e comparacao estrita (RF-04).
- Pre-parecer em rascunho com fontes citadas (RF-05).
- Human-in-the-loop via interrupt do LangGraph: o grafo pausa e espera a decisao do analista (RF-06).
- Trilha de auditoria com versao de prompt/modelo, custos e timestamps (RF-07).
- Retomada de execucao apos interrupcao, via checkpointing SqliteSaver por thread_id (RF-08).
- Streaming de progresso do grafo (RF-09), defesa contra prompt injection (RF-10), mascaramento de PII (RF-11) e modo demo sem custo com extrator injetavel (RF-12).

## 5. Explicitamente FORA de escopo

- **NAO decide aprovacao nem recusa** — toda decisao e do analista, via revisao humana obrigatoria.
- **Credito Pessoa Juridica (PJ)** — apenas PF nesta versao.
- **Scoring estatistico ou modelo de ML proprietario** de risco.
- **Integracao com bureaus reais** (Serasa, SPC ou equivalentes).
- **Aconselhamento juridico** de qualquer natureza.
- **Persistencia de PII em claro** — PII e sempre mascarada em logs e auditoria.
- **OCR limitado a Tesseract local** (pluggable) nesta versao, sem fallback a modelo de visao.

## 6. Premissas inegociaveis

- **P1** — O agente assiste o analista e nunca decide aprovacao/recusa; toda decisao passa por revisao humana (HITL obrigatorio).
- **P2** — O LLM orquestra; tools deterministicas calculam. Nenhum numero sai da cabeca do modelo.
- **P3** — Conteudo de documento e DADO, nunca instrucao (defesa contra prompt injection).
- **P4** — PII e mascarada em qualquer log ou trilha de auditoria.
- **P5** — Nenhum segredo no repositorio nem no historico; `.env` ignorado desde o commit zero, `.env.example` apenas com placeholders.

## 7. Metricas de sucesso

- **Custo**: <= US$0,01 por dossie, com Haiku e prompt caching (RNF-01).
- **Latencia**: media <= 5s por dossie, sem OCR (RNF-02).
- **Seguranca de PII**: 0 vazamentos de PII na trilha de auditoria (RNF-03).
- **Resistencia a injecao**: 0 obediencia a injecao no dataset adversarial (RNF-04).
- **Qualidade dos calculos**: cobertura de testes das tools deterministicas = 100% (RNF-05).

## 8. Principais riscos e mitigacoes

- **Alucinacao numerica** — todo numero vem de tools deterministicas, nunca do LLM (P2, RF-03; cobertura 100% por RNF-05).
- **Prompt injection** — conteudo de documento e tratado como dado, registrado e ignorado como instrucao (P3, RF-10; 0 obediencia por RNF-04).
- **Vazamento de PII** — mascaramento em todo log e na trilha de auditoria (P4, RF-11; 0 vazamentos por RNF-03).
- **Custo e latencia** — Haiku com prompt caching contem o custo por dossie (RNF-01) e mantem a latencia dentro do alvo (RNF-02).
