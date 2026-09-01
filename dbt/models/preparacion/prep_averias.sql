-- The four failure reports, errata included.
--
-- `nr` is NOT a key: two reports are «#1». Module 12 measured it and this
-- respects it, so the real key is the pair of number and start time.
SELECT
    nr,
    inicio,
    fin,
    horas,
    failure AS averia,
    severity AS gravedad,
    report AS parte
FROM {{ source('lago', 'averias') }}
