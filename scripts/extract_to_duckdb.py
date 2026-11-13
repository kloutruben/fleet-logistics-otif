import os
import duckdb
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DUCKDB_PATH = "data/duckdb/logistics_dw.duckdb"
TABELAS = [
    "veiculos",
    "motoristas",
    "rotas",
    "viagens",
    "entregas_itens",
    "abastecimentos_manutencoes"
]

def run_extraction():
    print("A conectar ao PostgreSQL (tms_db)...")
    pg_conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "tms_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "postgres")
    )

    os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
    duck_conn = duckdb.connect(DUCKDB_PATH)
    
    # Cria o schema raw (Camada Bronze)
    duck_conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    for tabela in TABELAS:
        print(f"A extrair tabela '{tabela}' -> raw.{tabela}...")
        df = pd.read_sql(f"SELECT * FROM {tabela};", pg_conn)
        
        # Adiciona timestamp de ingestão para auditoria
        df["_extracted_at"] = pd.Timestamp.now()
        
        # Carregamento idempotente na camada Bronze
        duck_conn.execute(f"CREATE OR REPLACE TABLE raw.{tabela} AS SELECT * FROM df;")
        
        qtd = duck_conn.execute(f"SELECT COUNT(*) FROM raw.{tabela}").fetchone()[0]
        print(f"   -> {qtd} registos carregados em raw.{tabela}.")

    pg_conn.close()
    duck_conn.close()
    print(f"\nIngestão concluída com sucesso em: {DUCKDB_PATH}")

if __name__ == "__main__":
    run_extraction()
