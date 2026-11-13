SELECT
    veiculo_id,
    placa,
    marca,
    modelo,
    marca || ' ' || modelo AS veiculo_completo,
    ano_fabricacao,
    capacidade_kg,
    consumo_medio_esperado_kml,
    km_atual,
    km_proxima_manutencao,
    (km_proxima_manutencao - km_atual) AS km_restante_manutencao,
    CASE
        WHEN km_atual >= km_proxima_manutencao THEN 'Crítico - Manutenção Vencida'
        WHEN (km_proxima_manutencao - km_atual) <= 1000 THEN 'Alerta - Próximo da Revisão'
        ELSE 'Normal'
    END AS status_manutencao
FROM {{ source('tms_raw', 'veiculos') }}
