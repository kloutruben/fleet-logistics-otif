import os
import random
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker('pt_PT')
random.seed(42)

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "tms_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS")
)
cur = conn.cursor()

print("1. A gerar Veículos...")
modelos = [
    ("Scania", "R450", 28000, 2.8),
    ("Volvo", "FH 540", 30000, 2.5),
    ("Mercedes-Benz", "Actros 2651", 27000, 2.7),
    ("DAF", "XF 480", 26000, 2.9),
    ("Iveco", "S-Way 480", 25000, 3.0)
]
veiculos_data = []
for i in range(1, 31):
    marca, modelo, cap, consumo = random.choice(modelos)
    placa = f"LD-{random.randint(10,99)}-{random.randint(10,99)}-{chr(random.randint(65,90))}{chr(random.randint(65,90))}"
    km_atual = random.randint(45000, 280000)
    # Alguns veículos propositadamente perto ou acima da manutenção
    km_prox = km_atual + random.choice([-450, 350, 850, 4500, 9000, 12000])
    veiculos_data.append((placa, modelo, marca, random.randint(2019, 2025), cap, consumo, km_atual, km_prox, 'Ativo'))

execute_values(cur, """
    INSERT INTO veiculos (placa, modelo, marca, ano_fabricacao, capacidade_kg, consumo_medio_esperado_kml, km_atual, km_proxima_manutencao, status_operacional)
    VALUES %s ON CONFLICT (placa) DO NOTHING
""", veiculos_data)

print("2. A gerar Motoristas...")
motoristas_data = []
for i in range(1, 46):
    motoristas_data.append((
        fake.name(),
        f"CNH-{random.randint(10000000, 99999999)}",
        random.choice(['C', 'D', 'E']),
        fake.date_between(start_date='-6y', end_date='-6m'),
        True
    ))
execute_values(cur, """
    INSERT INTO motoristas (nome, numero_licenca, categoria_cnh, data_admissao, ativo)
    VALUES %s ON CONFLICT (numero_licenca) DO NOTHING
""", motoristas_data)

print("3. A gerar Rotas...")
rotas_base = [
    ("RT-001", "Luanda (Porto)", "Benguela", 540, 8.5, 15.0),
    ("RT-002", "Luanda (Viana)", "Huambo", 605, 9.5, 12.0),
    ("RT-003", "Luanda", "Lubango", 920, 14.0, 20.0),
    ("RT-004", "Lobito", "Huambo", 320, 5.5, 8.0),
    ("RT-005", "Luanda", "Malanje", 390, 6.0, 10.0),
    ("RT-006", "Luanda", "Cabinda (Via Aérea/Marítima)", 480, 12.0, 45.0),
    ("RT-007", "Lubango", "Namibe", 180, 3.0, 5.0),
    ("RT-008", "Luanda", "Soyo", 450, 7.5, 14.0)
]
execute_values(cur, """
    INSERT INTO rotas (codigo_rota, origem, destino, distancia_estimada_km, tempo_estimado_horas, pedagio_estimado)
    VALUES %s ON CONFLICT (codigo_rota) DO NOTHING
""", rotas_base)
conn.commit()

cur.execute("SELECT veiculo_id, consumo_medio_esperado_kml, km_atual FROM veiculos")
veiculos_db = cur.fetchall()
cur.execute("SELECT motorista_id FROM motoristas")
motoristas_ids = [r[0] for r in cur.fetchall()]
cur.execute("SELECT rota_id, distancia_estimada_km, tempo_estimado_horas FROM rotas")
rotas_db = cur.fetchall()

print("4. A gerar 3.000 Viagens, Itens (In-Full) e Abastecimentos/Manutenções...")
start_date = datetime.now() - timedelta(days=365)

for _ in range(3000):
    v_id, consumo_esp, v_km = random.choice(veiculos_db)
    m_id = random.choice(motoristas_ids)
    r_id, dist_est, tempo_est = random.choice(rotas_db)
    dist_est = float(dist_est)
    tempo_est = float(tempo_est)

    data_saida = start_date + timedelta(days=random.randint(0, 364), hours=random.randint(5, 18))
    data_prevista = data_saida + timedelta(hours=tempo_est)

    # Simular atraso em ~22% das viagens (mais frequente na rota 3 e 6)
    prob_atraso = 0.38 if r_id in (3, 6) else 0.18
    if random.random() < prob_atraso:
        atraso_horas = random.uniform(1.5, 14.0)
        data_real = data_prevista + timedelta(hours=atraso_horas)
        status = 'Atrasada'
    else:
        adiantamento = random.uniform(-1.5, 0.5)
        data_real = data_prevista + timedelta(hours=adiantamento)
        status = 'Concluída'

    km_real = round(dist_est * random.uniform(0.98, 1.08), 2)
    frete = round(km_real * random.uniform(3.2, 4.8), 2)

    cur.execute("""
        INSERT INTO viagens (veiculo_id, motorista_id, rota_id, data_saida, data_prevista_entrega, data_real_entrega, km_percorrido_real, valor_frete_cobrado, status_viagem)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING viagem_id
    """, (v_id, m_id, r_id, data_saida, data_prevista, data_real, km_real, frete, status))
    viagem_id = cur.fetchone()[0]

    # Itens da entrega (In-Full falha em ~15% dos casos)
    qtd_sol = random.randint(10, 100)
    if random.random() < 0.15:
        qtd_ent = qtd_sol - random.randint(1, max(1, int(qtd_sol * 0.2)))
        motivo = random.choice(['Avaria no transporte', 'Falta em estoque na expedição', 'Divergência de conferência'])
    else:
        qtd_ent = qtd_sol
        motivo = None

    cur.execute("""
        INSERT INTO entregas_itens (viagem_id, sku_produto, descricao_produto, qtd_solicitada, qtd_entregue, motivo_divergencia)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (viagem_id, f"SKU-{random.randint(100,999)}", "Carga Paletizada Geral", qtd_sol, qtd_ent, motivo))

    # Abastecimento associado à viagem (alguns veículos gastam 20% a mais)
    fator_consumo = random.uniform(0.75, 0.85) if v_id % 5 == 0 else random.uniform(0.95, 1.05)
    consumo_real_kml = float(consumo_esp) * fator_consumo
    litros = round(km_real / consumo_real_kml, 2)
    valor_comb = round(litros * random.uniform(1.15, 1.35), 2)

    cur.execute("""
        INSERT INTO abastecimentos_manutencoes (veiculo_id, viagem_id, tipo_evento, data_evento, km_odometro, litros, valor_total, fornecedor)
        VALUES (%s, %s, 'Abastecimento', %s, %s, %s, %s, %s)
    """, (v_id, viagem_id, data_saida + timedelta(hours=2), v_km, litros, valor_comb, random.choice(['Sonangol', 'Pumangol', 'TotalEnergies'])))

# Adicionar manutenções periódicas
for v_id, _, v_km in veiculos_db:
    for m in range(random.randint(2, 5)):
        tipo_m = random.choice(['Manutenção Preventiva', 'Manutenção Corretiva'])
        valor_m = round(random.uniform(450, 2800), 2) if tipo_m == 'Manutenção Preventiva' else round(random.uniform(1200, 6500), 2)
        cur.execute("""
            INSERT INTO abastecimentos_manutencoes (veiculo_id, tipo_evento, data_evento, km_odometro, valor_total, fornecedor, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (v_id, tipo_m, start_date + timedelta(days=random.randint(10, 350)), v_km - random.randint(1000, 20000), valor_m, "Oficina Central Frota", "Revisão de sistema de travagem e motor"))

conn.commit()
cur.close()
conn.close()
print("Concluído! Dados inseridos com sucesso no PostgreSQL (tms_db).")
