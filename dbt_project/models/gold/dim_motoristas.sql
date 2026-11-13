SELECT
    motorista_id,
    nome AS nome_motorista,
    numero_licenca,
    categoria_cnh,
    data_admissao,
    ativo
FROM {{ source('tms_raw', 'motoristas') }}
