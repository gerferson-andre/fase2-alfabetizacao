## Ingestão batch e camada Bronze

### Escopo
Ingestão batch das 6 tabelas obrigatórias (`alunos`, `municipio`, `uf`, `meta_alfabetizacao_brasil`, `meta_alfabetizacao_uf`, `meta_alfabetizacao_municipio`) e do `dicionario`, do dataset `br_inep_avaliacao_alfabetizacao` (Base dos Dados), para o dataset `bronze` no BigQuery. O código está em `src/ingestao/ingestao_bronze.py`.

### Acesso à fonte: BigQuery direto
**Por que:** as tabelas já existem nativamente no BigQuery. Lê-las direto evita baixar e reenviar arquivos, e cada execução lê o estado atual da fonte. O dataset de destino fica na mesma localização da fonte (US), o que é necessário para a consulta funcionar.

**Custo (quantidades medidas em 22/11/2026):** uma execução completa processou cerca de 271,5 milhões de bytes (aproximadamente 259 MiB), medidos por dry run e confirmados nos jobs. Como origem e destino estão na mesma nuvem e localização, não houve transferência entre nuvens nem entre regiões. O ambiente é o sandbox do BigQuery (sem faturamento), então o custo desta execução foi zero; a projeção de custo do mesmo desenho em produção está na seção de FinOps.

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
Cada tabela ingerida gera uma linha na tabela `bronze.metricas_execucao` (BigQuery), com `run_id`, `etapa`, `tabela`, `inicio`, `fim`, `duracao_s`, `linhas_entrada`, `linhas_saida`, `status`, `job_id`, `bytes_processados` e `erro`. As linhas se acumulam entre execuções. Se uma etapa falhar, a métrica é gravada com status `FALHA` e o processo termina com erro. O formato final da tabela será alinhado com o restante do grupo.
**Não implementado nesta etapa:** alerta de falha (e-mail, webhook ou política de nuvem).

### Como executar
1. Clonar o repositório e criar um ambiente virtual: `python -m venv .venv`.
2. Instalar as dependências: `pip install -r requirements.txt`.
3. Copiar `.env.example` para `.env` e preencher `GCP_PROJECT_ID`, `BQ_LOCATION` e `BRONZE_DATASET`.
4. Autenticar: `gcloud auth application-default login`.
5. Criar o dataset `bronze` no BigQuery, na mesma localização da fonte (US).
6. Rodar: `python src/ingestao/ingestao_bronze.py` (todas as tabelas) ou, por exemplo, `python src/ingestao/ingestao_bronze.py uf dicionario` (só algumas).

### Limitações conhecidas
- No sandbox do BigQuery, as tabelas expiram 60 dias após a criação e não há DML nem streaming. As evidências de execução ficam no repositório (`evidencias/`) por esse motivo.
- Cada execução copia a tabela inteira (sem ingestão incremental), então o armazenamento cresce a cada execução.
- A Bronze só confere a contagem de linhas entre fonte e destino. As validações de qualidade ficam na camada Silver.
- A fonte tem valores nulos (por exemplo, colunas de proporção na tabela `uf`), que a Bronze preserva de propósito.