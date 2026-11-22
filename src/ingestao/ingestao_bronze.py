import os
import sys
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(override=True)  # o .env do repositório sempre tem prioridade

PROJETO = os.environ["GCP_PROJECT_ID"]
DATASET_BRONZE = os.environ.get("BRONZE_DATASET", "bronze")
LOCAL = os.environ.get("BQ_LOCATION", "US")
FONTE = "basedosdados.br_inep_avaliacao_alfabetizacao"

TABELAS = [
    "alunos", "municipio", "uf",
    "meta_alfabetizacao_brasil", "meta_alfabetizacao_uf",
    "meta_alfabetizacao_municipio", "dicionario",
]

TABELA_METRICAS = "metricas_execucao"

SCHEMA_METRICAS = [
    bigquery.SchemaField("run_id", "STRING"),
    bigquery.SchemaField("etapa", "STRING"),
    bigquery.SchemaField("tabela", "STRING"),
    bigquery.SchemaField("inicio", "TIMESTAMP"),
    bigquery.SchemaField("fim", "TIMESTAMP"),
    bigquery.SchemaField("duracao_s", "FLOAT"),
    bigquery.SchemaField("linhas_entrada", "INTEGER"),
    bigquery.SchemaField("linhas_saida", "INTEGER"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("job_id", "STRING"),
    bigquery.SchemaField("bytes_processados", "INTEGER"),
    bigquery.SchemaField("erro", "STRING"),
]

client = bigquery.Client(project=PROJETO, location=LOCAL)


def estimar_bytes(sql: str) -> int:
    """Dry run: calcula quantos bytes a consulta leria, sem executar."""
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    return client.query(sql, job_config=cfg).total_bytes_processed


def contar_linhas_fonte(tabela: str) -> int:
    q = f"SELECT COUNT(*) AS n FROM `{FONTE}.{tabela}`"
    return list(client.query(q).result())[0].n


def contar_linhas_destino(tabela: str, run_id: str) -> int:
    q = (f"SELECT COUNT(*) AS n FROM `{PROJETO}.{DATASET_BRONZE}.{tabela}` "
         f"WHERE _ingestion_id = '{run_id}'")
    return list(client.query(q).result())[0].n


def registrar_metrica(linha: dict):
    """Acrescenta uma linha na tabela de métricas (nunca sobrescreve)."""
    destino = f"{PROJETO}.{DATASET_BRONZE}.{TABELA_METRICAS}"
    cfg = bigquery.LoadJobConfig(
        schema=SCHEMA_METRICAS,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    client.load_table_from_json([linha], destino, job_config=cfg).result()


def ingerir(tabela: str, run_id: str) -> bigquery.QueryJob:
    destino = f"{PROJETO}.{DATASET_BRONZE}.{tabela}"
    sql = f"""
        SELECT *,
               '{run_id}' AS _ingestion_id,
               CURRENT_TIMESTAMP() AS _ingestion_ts,
               '{FONTE}.{tabela}' AS _source_table
        FROM `{FONTE}.{tabela}`
    """
    print(f"[{tabela}] bytes estimados: {estimar_bytes(sql)}")
    cfg = bigquery.QueryJobConfig(
        destination=destino,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    job = client.query(sql, job_config=cfg)
    job.result()
    print(f"[{tabela}] job_id={job.job_id} bytes_processados={job.total_bytes_processed}")
    return job


def ingerir_com_metricas(tabela: str, run_id: str):
    inicio = datetime.now(timezone.utc)
    metrica = {
        "run_id": run_id, "etapa": "bronze", "tabela": tabela,
        "inicio": inicio.isoformat(), "status": "FALHA",
        "linhas_entrada": None, "linhas_saida": None,
        "job_id": None, "bytes_processados": None, "erro": None,
    }
    try:
        metrica["linhas_entrada"] = contar_linhas_fonte(tabela)
        job = ingerir(tabela, run_id)
        metrica["linhas_saida"] = contar_linhas_destino(tabela, run_id)
        metrica["job_id"] = job.job_id
        metrica["bytes_processados"] = job.total_bytes_processed
        metrica["status"] = "SUCESSO"
        print(f"[{tabela}] linhas: fonte={metrica['linhas_entrada']} bronze={metrica['linhas_saida']}")
    except Exception as e:
        metrica["erro"] = str(e)[:500]
        raise  # IMPORTANTE: levanta de novo para o pipeline parar
    finally:
        fim = datetime.now(timezone.utc)
        metrica["fim"] = fim.isoformat()
        metrica["duracao_s"] = (fim - inicio).total_seconds()
        registrar_metrica(metrica)


if __name__ == "__main__":
    # Sem argumentos: ingere todas as tabelas.
    # Com argumentos: ingere só as indicadas (ex.: python ingestao_bronze.py uf dicionario)
    escolhidas = sys.argv[1:] or TABELAS
    invalidas = [t for t in escolhidas if t not in TABELAS]
    if invalidas:
        sys.exit(f"Tabela(s) desconhecida(s): {invalidas}. Válidas: {TABELAS}")

    run_id = str(uuid.uuid4())
    print("run_id:", run_id)
    for tabela in escolhidas:
        ingerir_com_metricas(tabela, run_id)
    print("Ingestão concluída.")