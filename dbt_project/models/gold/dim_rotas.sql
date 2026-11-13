SELECT
    rota_id,
    codigo_rota,
    origem,
    destino,
    origem || ' -> ' || destino AS trajeto,
    distancia_estimada_km,
    tempo_estimado_horas,
    pedagio_estimado
FROM {{ source('tms_raw', 'rotas') }}
