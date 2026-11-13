SELECT
    evento_id,
    veiculo_id,
    viagem_id,
    tipo_evento,
    CAST(data_evento AS DATE) AS data_evento,
    km_odometro,
    COALESCE(litros, 0) AS litros,
    valor_total,
    fornecedor
FROM {{ source('tms_raw', 'abastecimentos_manutencoes') }}
