import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()  # lê o arquivo .env
projeto = os.environ["GCP_PROJECT_ID"]

client = bigquery.Client(project=projeto, location="US")
job = client.query("SELECT 1 AS teste")
print("Resultado:", list(job.result())[0].teste)
print("job_id:", job.job_id)