SELECT
    viagem_id,
    veiculo_id,
    motorista_id,
    rota_id,
    data_viagem,
    km_percorrido_real,
    tempo_real_horas,
    desvio_entrega_horas,
    valor_frete_cobrado,
    qtd_solicitada,
    qtd_entregue,
    motivo_divergencia,
    is_on_time,
    is_in_full,
    CASE WHEN is_on_time = 1 AND is_in_full = 1 THEN 1 ELSE 0 END AS is_otif
FROM {{ ref('slv_viagens') }}
