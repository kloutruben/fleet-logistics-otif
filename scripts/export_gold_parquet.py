import os
import duckdb

DUCKDB_PATH = "data/duckdb/logistics_dw.duckdb"
EXPORT_DIR = "data/gold_export"

TABELAS_GOLD = [
    "dim_veiculos",
    "dim_motoristas",
    "dim_rotas",
    "fct_viagens",
    "fct_custos_frota"
]

def export_gold():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)

    for tabela in TABELAS_GOLD:
        out_path = os.path.join(EXPORT_DIR, f"{tabela}.parquet")
        conn.execute(f"COPY main_gold.{tabela} TO '{out_path}' (FORMAT PARQUET);")
        print(f"Exportado: {out_path}")

    conn.close()
    print("\nCamada Gold pronta para consumo no Power BI!")

if __name__ == "__main__":
    export_gold()
