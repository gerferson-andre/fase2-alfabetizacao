# Pipeline Híbrido para Análise da Alfabetização no Brasil

Tech Challenge - Fase 2 - FIAP / PosTech (AI Scientist)

Pipeline de dados (batch + streaming) em nuvem, na Arquitetura Medalhão (Bronze, Silver e Gold), sobre os dados públicos do indicador de alfabetização do INEP.

## Equipe:
- Gabriel Balbine de Andrades 
- Gerferson André Silva Costa 
- Giulliano Alves Souza Machado 
- Matheus da Silva Lima

> **Status em 22/11/2026:** ingestão batch e camada Bronze implementadas e executadas no BigQuery. As demais etapas estão listadas como pendentes no [checklist](#checklist-de-pendências). Este README só descreve como implementado o que existe no repositório.

## Sumário
1. [Contexto do desafio](#contexto-do-desafio)
2. [Fonte de dados](#fonte-de-dados)
3. [Arquitetura prevista](#arquitetura-prevista)
4. [O que já foi feito](#o-que-já-foi-feito)
5. [Ingestão batch e camada Bronze](#ingestão-batch-e-camada-bronze)
6. [Como executar](#como-executar)
7. [Checklist de pendências](#checklist-de-pendências)
8. [Limitações conhecidas](#limitações-conhecidas)

## Contexto do desafio

A alfabetização na infância é um dos pilares do desenvolvimento educacional, social e econômico do país. O **Compromisso Nacional Criança Alfabetizada** mobiliza União, estados, Distrito Federal e municípios para que as crianças estejam alfabetizadas até o final do 2º ano do ensino fundamental.

Para apoiar a definição de parâmetros nacionais, o INEP realizou em 2023 a **Pesquisa Alfabetiza Brasil**, que definiu o ponto de corte de **743 pontos** na escala de proficiência do Saeb: a partir dele, uma criança é considerada alfabetizada. Com base nesse parâmetro foi criado o **Indicador Criança Alfabetizada**, o percentual de estudantes que atingem esse patamar.

O Tech Challenge simula o trabalho de uma equipe de engenharia de dados em uma organização pública de análise educacional: integrar fontes heterogêneas (metas nacionais, estaduais e municipais, dados territoriais, microdados de alunos e indicadores) em um pipeline escalável, com qualidade, monitoramento e controle de custos, que sirva para dashboards, análises de desigualdade educacional e, na Fase 3, para treinar um modelo preditivo.

### Meta de 2030: duas leituras diferentes
- **Aspiração:** o Compromisso Nacional tem como aspiração a universalização da alfabetização até 2030.
- **Trajetória pactuada:** as tabelas oficiais trazem metas anuais mensuráveis de 2024 a 2030. Para a rede pública, a coluna `meta_alfabetizacao_2030` traz o valor 80.

Diretriz do projeto: ao calcular a distância até a meta, usar a **meta pactuada da fonte**. A leitura de universalização, se for apresentada, deve ser identificada como **cenário aspiracional**, sem misturar as duas leituras sem avisar.

### O que o pipeline precisa entregar
- Ingestão **batch** (histórico) e **streaming** (eventos simulados), com tratamento de evento inválido ou duplicado e coluna que identifique a origem do dado.
- Camadas **Bronze** (bruto, com histórico preservado), **Silver** (tratado e integrado) e **Gold** (analítica), usando todas as 6 entidades.
- **Qualidade de dados** com regras bloqueantes e informativas, taxa de correspondência dos JOINs e demonstração de uma execução falhando.
- **Monitoramento** com métricas persistidas, alerta de falha e latência medida de verdade.
- **FinOps** com tabela de custo baseada em quantidades medidas.
- Execução **real em nuvem**, com evidências, e **reprodutibilidade** a partir do README.

## Fonte de dados

Dataset `br_inep_avaliacao_alfabetizacao`, da plataforma [Base dos Dados](https://basedosdados.org), disponível no BigQuery. Volumes medidos em 22/11/2026:

| Entidade | Tabela | Conteúdo | Linhas | Tamanho (MiB) |
|---|---|---|---|---|
| Dados de alunos | `alunos` | microdado individual: proficiência, presença, caderno, alfabetizado, peso amostral | 3.867.999 | 256,1 |
| Município | `municipio` | indicador por município, ano, série e rede | 23.995 | 1,75 |
| UF | `uf` | indicador por UF, ano, série e rede | 145 | 0,01 |
| Meta Brasil | `meta_alfabetizacao_brasil` | trajetória nacional 2024-2030 | 3 | < 0,01 |
| Meta UF | `meta_alfabetizacao_uf` | trajetória estadual | 81 | 0,01 |
| Meta município | `meta_alfabetizacao_municipio` | trajetória municipal | 10.704 | 1,1 |
| Dicionário | `dicionario` | tradução dos códigos de rede, série, presença e demais categorias | 27 | < 0,01 |

Evidência: `evidencias/tamanho-tabelas-fonte.png` e `evidencias/explorando-tabelas.md`.

## Arquitetura prevista

Fluxo geral: fontes (BigQuery da Base dos Dados e eventos simulados) -> Bronze (bruto) -> Silver (limpo e integrado, com validações de qualidade) -> Gold (indicadores, meta vs resultado, evolução temporal e dataset para a Fase 3), com monitoramento e controle de custos atravessando as etapas.

**Implementado até agora:** fonte (batch) -> Bronze, no BigQuery. As demais etapas ainda não existem no repositório.

**Diagrama da arquitetura:** pendente. Será incluído quando refletir o que foi implementado.

## O que já foi feito

- Repositório criado e organizado, com `.env.example`, `.gitignore` e `requirements.txt`; credenciais e configuração local fora do Git.
- Projeto no Google Cloud configurado, em modo **sandbox** (sem faturamento), e dataset `bronze` criado no BigQuery, na mesma localização da fonte (US).
- **Ingestão batch das 7 tabelas** (as 6 entidades obrigatórias e o dicionário), executada na nuvem, com contagem de linhas conferida contra a fonte.
- **Bronze** com escrita por acréscimo (`WRITE_APPEND`), histórico preservado (provado na tabela `uf`) e colunas de rastreabilidade.
- **Métricas de execução** gravadas e acumuladas na tabela `bronze.metricas_execucao`.
- **Evidências** de execução (job_id, contagens e prints) na pasta `evidencias/`.
- Justificativa do acesso à fonte (custo e atualização), descrita abaixo.

## Ingestão batch e camada Bronze

### Escopo
Ingestão batch das 6 tabelas obrigatórias (`alunos`, `municipio`, `uf`, `meta_alfabetizacao_brasil`, `meta_alfabetizacao_uf`, `meta_alfabetizacao_municipio`) e do `dicionario`, do dataset `br_inep_avaliacao_alfabetizacao` (Base dos Dados), para o dataset `bronze` no BigQuery. O código está em `src/ingestao/ingestao_bronze.py`.

### Acesso à fonte: BigQuery direto
**Por que:** as tabelas já existem nativamente no BigQuery. Lê-las direto evita baixar e reenviar arquivos, e cada execução lê o estado atual da fonte. O dataset de destino fica na mesma localização da fonte (US), o que é necessário para a consulta funcionar.

**Custo (quantidades medidas em 22/11/2026):** uma execução completa processou cerca de 271,5 milhões de bytes (aproximadamente 259 MiB), medidos por dry run e confirmados nos jobs. Como origem e destino estão na mesma nuvem e localização, não houve transferência entre nuvens nem entre regiões. O ambiente é o sandbox do BigQuery (sem faturamento), então o custo desta execução foi zero; a projeção de custo do mesmo desenho em produção será apresentada na seção de FinOps.

**Quando a fonte for atualizada:** cada execução lê a versão atual da fonte e acrescenta uma cópia completa com um novo `_ingestion_id`; as versões anteriores continuam na Bronze. Consequência: linhas que não mudaram se repetem entre execuções, então a camada Silver deve usar a ingestão mais recente de cada tabela. Ainda não há detecção de mudanças incremental.

### Bronze: política de escrita e histórico
- Escrita com `WRITE_APPEND`: uma execução nunca apaga a anterior.
- Os dados são copiados sem transformação (nulos e valores da fonte são preservados).
- Colunas de rastreabilidade acrescentadas a cada tabela: `_ingestion_id` (identifica a execução), `_ingestion_ts` (momento da ingestão) e `_source_table` (tabela de origem).
- Prova de histórico: a tabela `uf` foi ingerida em duas execuções (22/11/2026, 16:26:54 e 16:37:58 UTC), cada uma com 145 linhas, e as duas coexistem na Bronze. Evidência: `evidencias/bronze-uf-historico.png`.

### Volume ingerido (execução completa de 22/11/2026)
| Tabela | Linhas (fonte = Bronze) | Bytes processados |
|---|---|---|
| alunos | 3.867.999 | 268.545.240 |
| municipio | 23.995 | 1.832.061 |
| meta_alfabetizacao_municipio | 10.704 | 1.151.232 |
| uf | 145 | 10.330 |
| meta_alfabetizacao_uf | 81 | 7.374 |
| dicionario | 27 | 1.174 |
| meta_alfabetizacao_brasil | 3 | 270 |

Os `job_id` de cada tabela estão em `evidencias/bronze-execucao-completa.txt`.

### Métricas de execução
Cada tabela ingerida gera uma linha na tabela `bronze.metricas_execucao` (BigQuery), com `run_id`, `etapa`, `tabela`, `inicio`, `fim`, `duracao_s`, `linhas_entrada`, `linhas_saida`, `status`, `job_id`, `bytes_processados` e `erro`. As linhas se acumulam entre execuções. Se uma etapa falhar, a métrica é gravada com status `FALHA` e o processo termina com erro. Evidência: `evidencias/bronze-metricas-execucao.png`.

Observação: `duracao_s` inclui as consultas de contagem e a gravação da própria métrica, então nas tabelas pequenas ela é dominada por esse custo fixo (cerca de 5 s), e não pela cópia dos dados.

O formato final da tabela será alinhado com o restante do pipeline. **Não implementado nesta etapa:** alerta de falha (e-mail, webhook ou política de nuvem).

## Como executar

1. Clonar o repositório e criar um ambiente virtual: `python -m venv .venv`.
2. Instalar as dependências: `pip install -r requirements.txt`.
3. Copiar `.env.example` para `.env` e preencher `GCP_PROJECT_ID`, `BQ_LOCATION` e `BRONZE_DATASET`.
4. Autenticar: `gcloud auth application-default login`.
5. Criar o dataset `bronze` no BigQuery, na mesma localização da fonte (US).
6. Rodar: `python src/ingestao/ingestao_bronze.py` (todas as tabelas) ou, por exemplo, `python src/ingestao/ingestao_bronze.py uf dicionario` (só algumas).

Passo a passo ainda não testado em um clone limpo (ver checklist).

## Checklist de pendências

Marque `[x]` quando o item estiver pronto **e** descrito neste README. Itens marcados como (diferencial) não são obrigatórios, mas elevam a entrega.

### Decisões de arquitetura
- [ ] Confirmar o acesso à fonte direto pelo BigQuery como decisão do grupo
- [ ] Decidir o projeto de nuvem definitivo e se o ambiente segue no sandbox ou passa a ter faturamento
- [ ] Definir o formato único da tabela de métricas de execução
- [ ] Fechar o esquema do Gold (contrato entre as camadas)
- [ ] Diagrama da arquitetura refletindo o que foi implementado

### Ingestão batch e Bronze
- [x] Ingestão batch das 6 tabelas e do dicionário
- [x] Bronze com append e histórico preservado (política descrita e provada)
- [x] Rastreabilidade da origem (`_ingestion_id`, `_ingestion_ts`, `_source_table`)
- [x] Justificativa do acesso à fonte (custo e atualização) no README
- [x] Evidências de execução na nuvem (job_id e contagens de linhas)

### Silver
- [ ] Limpeza, padronização de nomes e tipos
- [ ] Uso do dicionário para traduzir códigos (sem inventar correspondências)
- [ ] Normalização das chaves e integração das 6 entidades
- [ ] Usar a ingestão mais recente de cada tabela da Bronze
- [ ] Preservar nulos (não preencher com zero) e usar categoria explícita "desconhecido" para códigos novos, com check de contagem zero

### Qualidade de dados
- [ ] Regras de duplicidade, ausentes, chaves de relacionamento e consistência entre tabelas
- [ ] Classificação das regras em bloqueantes e informativas
- [ ] Taxa de correspondência dos JOINs, com limiar definido e justificado
- [ ] Interromper a execução quando uma regra bloqueante falhar, antes de publicar a camada seguinte
- [ ] Resultado das validações persistido
- [ ] Demonstração de uma execução falhando

### Streaming
- [ ] Mecanismo de mensageria ou recepção de eventos (pode ser simulado)
- [ ] Processamento incremental (micro-lotes ou contínuo)
- [ ] Tratamento de evento inválido e duplicado
- [ ] Latência medida de fato (carimbo de produção diferente do de ingestão)
- [ ] Coluna que identifica a origem (oficial vs simulado)
- [ ] Diferença de latência, frequência e garantias em relação ao batch, explicada no README
- [ ] Evento chegando até a camada analítica

### Gold
- [ ] Indicadores por município e UF
- [ ] Meta vs resultado com terceiro estado "sem meta" (ausência de meta é diferente de não atingir)
- [ ] Comparar resultado e meta apenas no mesmo recorte de rede e série
- [ ] Agregações ponderadas por alunos (média simples entre municípios não é o indicador nacional)
- [ ] Evolução temporal do indicador
- [ ] Dataset para a Fase 3, sem vazamento de alvo
- [ ] Validação cruzada: recalcular a taxa a partir de `alunos` (peso amostral, denominador = alunos avaliados) e comparar com o indicador oficial (diferencial)

### Monitoramento
- [ ] Métricas persistidas de todas as etapas (duração, linhas de entrada e saída, status)
- [ ] Alerta de falha (e-mail, webhook ou política de nuvem)
- [ ] Latência do pipeline medida
- [ ] README responde: em produção, quem descobre que o pipeline quebrou, e em quanto tempo?

### FinOps
- [ ] Tabela de estimativa (serviço, unidade, quantidade medida, preço unitário, custo mensal projetado)
- [ ] Se o ambiente for sandbox, informar isso e projetar o custo do mesmo desenho em produção
- [ ] Boas práticas aplicadas e descritas (seleção de colunas, partição, formato colunar)

### Cloud, reprodutibilidade e repositório
- [x] Bronze executada na nuvem com evidências
- [ ] Demais etapas executadas na nuvem, com evidências
- [ ] Teste do passo a passo em um clone limpo
- [ ] Orquestração com dependência, retentativa e agendamento (diferencial)
- [ ] Infraestrutura como código (diferencial)
- [ ] Testes automatizados das funções de transformação (diferencial)
- [ ] Investigação documentada de uma anomalia nos dados (diferencial)

### Documentação e entrega
- [ ] Seção de tecnologias e decisões arquiteturais (batch vs streaming, data lake vs warehouse, custo vs performance)
- [ ] Seção de monitoramento e FinOps
- [ ] Seção de aplicação em IA (predição, desigualdade educacional, políticas públicas)
- [ ] Limitações conhecidas consolidadas
- [ ] Vídeo executivo de até 5 minutos, com link neste README

## Limitações conhecidas

- No sandbox do BigQuery, as tabelas expiram 60 dias após a criação e não há DML nem streaming. As evidências de execução ficam no repositório (`evidencias/`) por esse motivo.
- Cada execução copia a tabela inteira (sem ingestão incremental), então o armazenamento cresce a cada execução.
- As colunas de rastreabilidade aumentam o tamanho da Bronze: a tabela `alunos` ocupa cerca de 621 MiB, contra 256 MiB na fonte.
- A Bronze só confere a contagem de linhas entre fonte e destino. As validações de qualidade ficam na camada Silver.
- A fonte tem valores nulos (por exemplo, colunas de proporção na tabela `uf`), que a Bronze preserva de propósito.
- Esta lista será ampliada conforme as demais etapas forem implementadas.