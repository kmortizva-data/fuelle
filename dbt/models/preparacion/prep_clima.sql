-- Porto weather, hour by hour.
SELECT
    hora,
    day,
    temperatura,
    humedad,
    lluvia
FROM {{ source('lago', 'clima') }}
