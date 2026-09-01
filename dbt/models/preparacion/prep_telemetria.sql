-- The silver layer entering dbt, with the columns gold needs.
--
-- A view and not a table on purpose: it does not copy 1,841,760 rows, it only
-- names them. What gets materialised are the three gold tables.
SELECT
    timestamp,
    day,
    medido,
    dudoso,
    lecturas,
    TP2,
    TP3,
    Oil_temperature,
    Motor_current,
    DV_eletric,
    COMP,
    LPS
FROM {{ source('lago', 'plata') }}
