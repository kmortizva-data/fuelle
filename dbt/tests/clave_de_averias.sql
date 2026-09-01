-- The key of the reports is the pair, not the number.
--
-- This is a «singular» test: a SQL file that must return zero rows, exactly the
-- shape of module 16's contract. You write one when the promise does not fit in
-- the four dbt ships with.
SELECT nr, inicio, count(*) AS veces
FROM {{ ref('oro_averias') }}
GROUP BY nr, inicio
HAVING count(*) > 1
