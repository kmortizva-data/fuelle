-- Telemetry brought down to the weather's rhythm, and crossed with it.
--
-- Two `ref()`, so this node has two arrows coming in. It is module 15's
-- decision: to cross two sources you bring the fast one down to the grain of
-- the slow one, and here the slow one is the weather.
WITH por_hora AS (
    SELECT
        time_bucket(INTERVAL 1 HOUR, timestamp) AS hora,
        round(avg(Oil_temperature), 2)          AS aceite,
        round(avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END), 4) AS carga,
        count(*)                                AS lecturas
    FROM {{ ref('prep_telemetria') }}
    WHERE medido
    GROUP BY hora
)
SELECT
    h.hora,
    h.aceite,
    h.carga,
    h.lecturas,
    c.temperatura AS calle,
    c.humedad,
    round(h.aceite - c.temperatura, 2) AS aceite_sobre_calle
FROM por_hora h
JOIN {{ ref('prep_clima') }} c ON c.hora = h.hora
