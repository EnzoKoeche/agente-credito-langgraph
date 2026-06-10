# Matriz de Rastreabilidade

Esta matriz conecta, de ponta a ponta, cada requisito do projeto **agente-credito-langgraph** aos artefatos que o realizam (casos de uso), o executam (nos do grafo LangGraph) e o comprovam (evals e testes pytest). O objetivo e garantir que nenhum requisito fique orfao: todo requisito funcional aponta para **pelo menos um eval OU um teste pytest**, e todo requisito nao-funcional possui uma verificacao associada. A convencao de status segue tres estados progressivos: **planejado** (especificado, ainda nao implementado — estado inicial de todas as celulas de eval/teste deste documento), **implementado** (artefato existe e executa) e **verificado** (artefato executa e passa, comprovando o requisito). Enquanto o codigo nao for escrito, todas as celulas de verificacao permanecem como **planejado**.

## Matriz principal: RF -> UC -> No(s) do grafo -> Eval(s) -> Teste(s) pytest -> Status

| RF | Descricao | Caso(s) de Uso | No(s) do grafo | Eval(s) | Teste(s) pytest | Status |
|----|-----------|----------------|----------------|---------|-----------------|--------|
| RF-01 | Ingestao multi-formato (txt, PDF com texto, PDF escaneado, imagem) | UC-01 | n1 | EVAL-G2 | TEST-GRAPH-ROUTE | planejado |
| RF-02 | Extracao estruturada validada por schema Pydantic | UC-01 | n2, n3 | EVAL-DET-04 | TEST-EXTRACAO-SCHEMA | planejado |
| RF-03 | Indicadores via tools deterministicas (comprometimento, capacidade, simulacao de parcela) | UC-01 | n4 | EVAL-DET-06 | TEST-TOOLS-INDIC, TEST-TOOLS-SIMUL | planejado |
| RF-04 | Deteccao de inconsistencias por discrepancia relativa, limiares 0,30/0,50, comparacao estrita | UC-02 | n5 | EVAL-DET-01, EVAL-DET-02, EVAL-DET-03, EVAL-DET-07 | TEST-INCONS-LIMIAR | planejado |
| RF-05 | Pre-parecer com fontes citadas | UC-01 | n6 | EVAL-PAGA-HALU | TEST-TOOLS-INDIC | planejado |
| RF-06 | Human-in-the-loop via interrupt do LangGraph | UC-03 | n7 | EVAL-G1 | TEST-CHECKPOINT-RESUME | planejado |
| RF-07 | Trilha de auditoria com versao de prompt/modelo, custos e timestamps | UC-04 | n8 | EVAL-PAGA-PII | TEST-PII-MASK | planejado |
| RF-08 | Retomada de execucao apos interrupcao (checkpointing SqliteSaver por thread_id) | UC-05 | n7, n8 | EVAL-G1 | TEST-CHECKPOINT-RESUME | planejado |
| RF-09 | Streaming de progresso do grafo (modo values/updates) | UC-01 | n1, n2, n3, n4, n5, n6, n7, n8 | — | TEST-STREAM | planejado |
| RF-10 | Defesa contra prompt injection (conteudo de documento tratado como dado) | UC-01, UC-02 | n2 | EVAL-PAGA-INJ | TEST-INJ-DEFENSE | planejado |
| RF-11 | Mascaramento de PII em logs e na trilha de auditoria | UC-04 | n8 | EVAL-PAGA-PII | TEST-PII-MASK | planejado |
| RF-12 | Modo demo sem custo (extrator injetavel/mock) | UC-01 | n2 | — | TEST-DEMO-MODE | planejado |

> Verificacao de cobertura: RF-09 e RF-12 nao possuem eval associado, mas ambos apontam para um teste pytest (TEST-STREAM e TEST-DEMO-MODE, respectivamente), satisfazendo a regra de "pelo menos um eval OU um teste" por requisito. Todos os demais RFs possuem eval e teste.

## Matriz secundaria: RNF -> Verificacao (eval/teste) -> Status

| RNF | Alvo numerico / criterio | Verificacao | Status |
|-----|--------------------------|-------------|--------|
| RNF-01 | Custo <= US$0,01 por dossie (Haiku + prompt caching) | EVAL-PAGA-HALU, EVAL-PAGA-INJ, EVAL-PAGA-PII (guard de custo --sanity/--full mede custo por dossie) | planejado |
| RNF-02 | Latencia media <= 5s por dossie (sem OCR) | Timestamps de auditoria (media no dataset fixo, excluindo OCR), TEST-STREAM | planejado |
| RNF-03 | 0 vazamentos de PII na trilha de auditoria | EVAL-PAGA-PII, TEST-PII-MASK | planejado |
| RNF-04 | 0 obediencia a injecao no dataset adversarial | EVAL-PAGA-INJ, TEST-INJ-DEFENSE | planejado |
| RNF-05 | Cobertura de testes das tools deterministicas = 100% | TEST-TOOLS-INDIC, TEST-TOOLS-SIMUL, TEST-INCONS-LIMIAR | planejado |
| RNF-06 | Retomada pos-interrupt restaura estado identico (hash de estado igual) | EVAL-G1, TEST-CHECKPOINT-RESUME | planejado |
| RNF-07 | Roteamento das arestas condicionais correto em 100% do dataset de grafo | EVAL-G2, TEST-GRAPH-ROUTE | planejado |
| RNF-08 | Nenhum segredo no repositorio nem no historico (.env ignorado desde o commit zero) | .gitignore desde o commit zero + secret scan do historico + inspecao de .env.example | planejado |
| RNF-09 | Reprodutibilidade: Python 3.12, dependencias pinadas em requirements.txt | Suite pytest completa executada em Python 3.12 com requirements.txt pinado | planejado |

## Cobertura das arestas condicionais

| Aresta | Roteamento | Eval | Teste pytest | Status |
|--------|------------|------|--------------|--------|
| e1 | ingestao -> OCR (PDF sem texto/imagem) ou extracao direta (txt/PDF com texto) | EVAL-G2 | TEST-GRAPH-ROUTE | planejado |
| e2 | validacao_confianca -> escalacao direta para revisao_humana se confianca < 0,6, senao indicadores | EVAL-G2 | TEST-GRAPH-ROUTE | planejado |
| e3 | revisao_humana -> registro_auditoria (aprovado) ou registro_auditoria (devolvido, com motivo) | EVAL-G2 | TEST-GRAPH-ROUTE | planejado |
