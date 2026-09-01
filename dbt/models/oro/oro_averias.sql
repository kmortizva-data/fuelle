-- The four reports, each with what the compressor actually did meanwhile.
--
-- The JOIN goes by interval and not by equality, because telemetry has a day
-- and a report has a range. Module 12.
SELECT
    a.nr,
    a.inicio,
    a.fin,
    a.horas                          AS horas_del_parte,
    a.averia,
    count(c.dia)                     AS dias_con_datos,
    round(sum(c.horas_de_carga), 1)  AS horas_de_carga,
    sum(c.arranques)                 AS arranques,
    round(avg(c.aceite_medio), 1)    AS aceite_medio
FROM {{ ref('prep_averias') }} a
LEFT JOIN {{ ref('oro_ciclo_diario') }} c
       ON c.dia BETWEEN CAST(a.inicio AS DATE) AND CAST(a.fin AS DATE)
GROUP BY a.nr, a.inicio, a.fin, a.horas, a.averia
