-- One day per row, with what the twin will need from each of them.
--
-- This is the table the project hangs from: the duty cycle is where the leak
-- shows, because pressure is held by the control loop and does not move.
--
-- The `ref()` below is what makes dbt know this comes after prep_telemetria.
-- Nobody tells it, and the graph comes from there.
WITH lecturas AS (
    SELECT
        day,
        DV_eletric,
        lag(DV_eletric) OVER (PARTITION BY day ORDER BY timestamp) AS antes,
        medido,
        dudoso,
        Oil_temperature
    FROM {{ ref('prep_telemetria') }}
    WHERE medido
)
SELECT
    day                                                          AS dia,
    count(*)                                                     AS lecturas,
    round(count(*) * 100.0 / 8640, 1)                            AS por_ciento_del_dia,
    count(*) > 0.9 * 8640                                        AS dia_completo,
    round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2)
                                                                 AS horas_de_carga,
    sum(CASE WHEN antes = 0 AND DV_eletric = 1 THEN 1 ELSE 0 END) AS arranques,
    round(avg(Oil_temperature), 2)                               AS aceite_medio,
    sum(CASE WHEN dudoso THEN 1 ELSE 0 END)                      AS lecturas_dudosas
FROM lecturas
GROUP BY day
