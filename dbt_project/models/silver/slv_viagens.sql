WITH viagens AS (
    SELECT * FROM {{ source('tms_raw', 'viagens') }}
    WHERE status_viagem != 'Cancelada'
),
itens AS (
    SELECT
        viagem_id,
        SUM(qtd_solicitada) AS total_qtd_solicitada,
        SUM(qtd_entregue) AS total_qtd_entregue,
        MAX(motivo_divergencia) AS motivo_divergencia
    FROM {{ source('tms_raw', 'entregas_itens') }}
    GROUP BY 1
)
SELECT
    v.viagem_id,
    v.veiculo_id,
    v.motorista_id,
    v.rota_id,
    CAST(v.data_saida AS DATE) AS data_viagem,
    v.data_saida,
    v.data_prevista_entrega,
    v.data_real_entrega,
    ROUND(EPOCH(v.data_real_entrega - v.data_saida) / 3600.0, 2) AS tempo_real_horas,
    ROUND(EPOCH(v.data_real_entrega - v.data_prevista_entrega) / 3600.0, 2) AS desvio_entrega_horas,
    v.km_percorrido_real,
    v.valor_frete_cobrado,
    v.status_viagem,
    COALESCE(i.total_qtd_solicitada, 0) AS qtd_solicitada,
    COALESCE(i.total_qtd_entregue, 0) AS qtd_entregue,
    i.motivo_divergencia,
    CASE WHEN v.data_real_entrega <= v.data_prevista_entrega THEN 1 ELSE 0 END AS is_on_time,
    CASE WHEN COALESCE(i.total_qtd_entregue, 0) >= COALESCE(i.total_qtd_solicitada, 0) THEN 1 ELSE 0 END AS is_in_full
FROM viagens v
LEFT JOIN itens i ON v.viagem_id = i.viagem_id
