WITH viagens_veiculo AS (
    SELECT
        veiculo_id,
        data_viagem,
        SUM(km_percorrido_real) AS km_rodado_dia,
        SUM(valor_frete_cobrado) AS receita_frete_dia
    FROM {{ ref('slv_viagens') }}
    GROUP BY 1, 2
),
custos_veiculo AS (
    SELECT
        veiculo_id,
        data_evento,
        SUM(CASE WHEN tipo_evento = 'Abastecimento' THEN valor_total ELSE 0 END) AS custo_combustivel,
        SUM(CASE WHEN tipo_evento = 'Abastecimento' THEN litros ELSE 0 END) AS litros_abastecidos,
        SUM(CASE WHEN tipo_evento LIKE 'Manutenção%' THEN valor_total ELSE 0 END) AS custo_manutencao,
        SUM(valor_total) AS custo_total_dia
    FROM {{ ref('slv_custos_frota') }}
    GROUP BY 1, 2
)
SELECT
    COALESCE(v.veiculo_id, c.veiculo_id) AS veiculo_id,
    COALESCE(v.data_viagem, c.data_evento) AS data_referencia,
    COALESCE(v.km_rodado_dia, 0) AS km_rodado,
    COALESCE(v.receita_frete_dia, 0) AS receita_frete,
    COALESCE(c.custo_combustivel, 0) AS custo_combustivel,
    COALESCE(c.litros_abastecidos, 0) AS litros_abastecidos,
    COALESCE(c.custo_manutencao, 0) AS custo_manutencao,
    COALESCE(c.custo_total_dia, 0) AS custo_total,
    CASE
        WHEN COALESCE(v.km_rodado_dia, 0) > 0 THEN ROUND(COALESCE(c.custo_total_dia, 0) / v.km_rodado_dia, 2)
        ELSE 0
    END AS custo_por_km,
    CASE
        WHEN COALESCE(c.litros_abastecidos, 0) > 0 THEN ROUND(COALESCE(v.km_rodado_dia, 0) / c.litros_abastecidos, 2)
        ELSE NULL
    END AS consumo_real_kml
FROM viagens_veiculo v
FULL OUTER JOIN custos_veiculo c
    ON v.veiculo_id = c.veiculo_id AND v.data_viagem = c.data_evento
