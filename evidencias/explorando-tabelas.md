# Tabelas da fonte: tamanho e volume

Fonte: `basedosdados.br_inep_avaliacao_alfabetizacao`
Consulta feita em 22/11/2026, no BigQuery (modo sandbox, sem faturamento).
Print: `tamanho-tabelas-fonte.png`

| Tabela | Linhas | Tamanho (MB) |
|---|---|---|
| alunos | 3.867.999 | 256,1 |
| municipio | 23.995 | 1,75 |
| meta_alfabetizacao_municipio | 10.704 | 1,1 |
| uf | 145 | 0,01 |
| meta_alfabetizacao_uf | 81 | 0,01 |
| dicionario | 27 | < 0,01 |
| meta_alfabetizacao_brasil | 3 | < 0,01 |

Total aproximado: 260 MB e 3.903.954 linhas.

## Estimativa de bytes (dry run) de `SELECT *`

| Tabela | Estimativa |
|---|---|
| uf | 10,09 KB |
| alunos | 268.545.240 bytes (256,1 MiB) |

## Observações

- Limites gratuitos do sandbox usados como referência: 10 GB de armazenamento e 1 TB de consultas por mês, com tabelas expirando em 60 dias.
- Os tamanhos acima são o armazenamento (`size_bytes` da tabela `__TABLES__`). A estimativa de bytes de um `SELECT *` pode diferir um pouco.
- job_id: bb72a21c-71a3-42c3-882a-6c1f65ad09b3

## Primeira ingestão da Bronze (tabela uf)

- Data: 22/11/2026
- run_id: d8b6fb57-2b8f-4673-9ed9-3c46f9475146
- Linhas na Bronze: 145
- Prints: `bronze-uf-contagem.png` e `bronze-uf-colunas.png`

## Reprocesso da tabela uf (prova de histórico)

- 2 execuções na Bronze: 22/11/2026 16:26:54 UTC e 16:37:58 UTC, com 145 linhas cada
- Print: `bronze-uf-historico.png`
- Política: `WRITE_APPEND`, a segunda execução não apagou a primeira