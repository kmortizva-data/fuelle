"""The weather in Porto, hour by hour, from a free API. Module 15.

The compressor takes its air from the street, so the street's temperature and
humidity are part of its physics: warmer air holds more water, and water in the
line is what corrodes a pneumatic panel. This is the second source of the lake
and the first one that does not come from the machine.

It matters for the course beyond the physics, because it brings problems the
telemetry does not have:

  1. **Another frequency.** Weather is hourly and telemetry is every ten
     seconds. Crossing them means deciding what "the temperature at 06:00:12"
     means, and that decision is the module.
  2. **Another owner.** Nobody here controls this API. It can change, rate limit
     or disappear, so what it returns gets stored raw and the ingestion is
     idempotent, with the fingerprint rules of module 5.
  3. **Another timezone.** Everything is asked in UTC on purpose. Mixing local
     time with UTC is the classic way to shift a whole dataset by an hour and
     never notice.

Open-Meteo's historical archive is free and needs no key. The licence is CC BY
4.0, the same as the compressor's data, and it gets cited.

Run:  .venv\\Scripts\\python.exe src\\ingest\\weather.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

# La red de esta máquina intercepta el SSL, así que truststore va antes que
# cualquier petición. Sin esto la descarga falla con un error de certificado
# que no dice nada útil.
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from escritura import un_solo_hilo  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RAW = PROJECT / "data" / "clima_oporto.json"
BRONZE = PROJECT / "lake" / "bronze" / "weather"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m15_clima.json"

# El Metro de Oporto. Coordenadas del centro de la ciudad, que es donde circula.
LAT, LON = 41.15, -8.61
DESDE, HASTA = "2020-02-01", "2020-09-01"
SEÑALES = ["temperature_2m", "relative_humidity_2m", "precipitation"]

URL = ("https://archive-api.open-meteo.com/v1/archive"
       f"?latitude={LAT}&longitude={LON}"
       f"&start_date={DESDE}&end_date={HASTA}"
       f"&hourly={','.join(SEÑALES)}&timezone=UTC")


def descarga() -> dict:
    """Se baja una vez y se guarda. Las siguientes corridas leen el fichero.

    Es la regla del módulo 5 aplicada a una fuente que no controlamos: pedirle
    lo mismo cada vez a un servicio ajeno es maleducado y frágil, y además haría
    que el resultado dependiera de que hoy esté levantado.
    """
    if RAW.exists():
        print(f"  ya estaba descargado: {RAW.relative_to(PROJECT)}")
        return json.loads(io.open(RAW, encoding="utf-8").read())

    print(f"  pidiendo a archive-api.open-meteo.com el clima de {DESDE} a {HASTA}...")
    with urllib.request.urlopen(URL, timeout=120) as r:
        crudo = r.read()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(crudo)
    print(f"  {len(crudo) / 1024:.1f} KB guardados en {RAW.relative_to(PROJECT)}")
    return json.loads(crudo)


def vista_del_clima(con: duckdb.DuckDBPyConnection, datos: dict) -> None:
    """El JSON de la API como una tabla `clima`, una fila por hora."""
    con.execute(f"""
        CREATE VIEW clima AS
        SELECT CAST(unnest({datos['hourly']['time']!r}) AS TIMESTAMP) AS hora,
               unnest({datos['hourly'][SEÑALES[0]]!r}) AS temperatura,
               unnest({datos['hourly'][SEÑALES[1]]!r}) AS humedad,
               unnest({datos['hourly'][SEÑALES[2]]!r}) AS lluvia
    """)


def escribe_bronce(con: duckdb.DuckDBPyConnection) -> None:
    """El clima al lago, una carpeta por día. Con un hilo: ver src/escritura.py."""
    import shutil

    if BRONZE.exists():
        shutil.rmtree(BRONZE)
    BRONZE.parent.mkdir(parents=True, exist_ok=True)
    with un_solo_hilo(con):
        con.execute(f"COPY (SELECT *, CAST(hora AS DATE) AS day FROM clima) "
                    f"TO '{BRONZE.as_posix()}' "
                    f"(FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, "
                    f"COMPRESSION ZSTD)")


def construye() -> dict:
    """Bajar el clima si no está y escribir su bronce. Nada más, y sin la plata.

    Es lo que orquesta el módulo 29. `main()` hace esto mismo y además cruza el
    clima con la plata para la pregunta del módulo 15, y eso solo se puede hacer
    con la plata construida. La primera versión mezclaba las dos cosas, y cuando
    el orquestador la corrió antes que la plata escribió `null` en siete cifras
    publicadas sin quejarse.
    """
    con = duckdb.connect()
    vista_del_clima(con, descarga())
    escribe_bronce(con)
    horas = con.sql("SELECT count(*) FROM clima").fetchone()[0]
    con.close()
    return {"horas": horas}


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero: las "
                         "correlaciones del módulo 15 cruzan el clima con ella, y sin ella "
                         "saldrían vacías.")
    datos = descarga()
    huella = hashlib.sha256(RAW.read_bytes()).hexdigest()

    con = duckdb.connect()
    vista_del_clima(con, datos)

    resumen = con.sql("""
        SELECT count(*) AS horas,
               count(temperatura) AS con_temperatura,
               round(min(temperatura), 1) AS min_temp,
               round(max(temperatura), 1) AS max_temp,
               round(avg(temperatura), 1) AS media_temp,
               round(avg(humedad), 1) AS media_humedad
        FROM clima
    """).fetchone()

    escribe_bronce(con)

    # La pregunta física del módulo: ¿explica la calle la temperatura del aceite?
    #
    #     Se cruza a la hora, que es la frecuencia de la fuente más lenta. La
    #     comparación con la correlación de la carga está a propósito: sirve para
    #     saber si el clima aporta algo que la máquina no explica ya.
    con.execute(f"CREATE VIEW plata AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")
    correlacion = con.sql("""
            WITH por_hora AS (
                SELECT time_bucket(INTERVAL 1 HOUR, timestamp) AS hora,
                       avg(Oil_temperature) AS aceite,
                       avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END) AS carga
                FROM plata WHERE medido GROUP BY hora
            )
            SELECT count(*),
                   round(corr(c.temperatura, p.aceite), 3),
                   round(corr(p.carga, p.aceite), 3),
                   round(avg(p.aceite - c.temperatura), 1)
            FROM por_hora p JOIN clima c ON c.hora = p.hora
        """).fetchone()

    # La meseta del aceite el día de la avería #3, que la lección cita al mirar
    # la figura. Medida aquí en vez de leída del dibujo, que es de donde salió
    # la primera versión de esa frase.
    meseta = con.sql("""
        SELECT round(avg(Oil_temperature), 1),
               round(min(Oil_temperature), 1),
               round(max(Oil_temperature), 1)
        FROM plata
        WHERE medido AND timestamp >= TIMESTAMP '2020-06-05 10:00:00'
                    AND timestamp <  TIMESTAMP '2020-06-06 00:00:00'
    """).fetchone()

    # Las tres frecuencias que va a tener el lago, para la figura del módulo.
    lecturas = con.sql(
        f"SELECT count(*) FROM read_parquet("
        f"'{(PROJECT / 'lake' / 'bronze' / 'telemetry').as_posix()}/**/*.parquet')"
    ).fetchone()[0]

    payload = {
        "url": URL,
        "latitud": LAT, "longitud": LON,
        "desde": DESDE, "hasta": HASTA,
        "sha256": huella,
        "kb_descargados": round(RAW.stat().st_size / 1024, 1),
        "horas": resumen[0],
        "horas_con_temperatura": resumen[1],
        "temperatura_minima": float(resumen[2]),
        "temperatura_maxima": float(resumen[3]),
        "temperatura_media": float(resumen[4]),
        "humedad_media": float(resumen[5]),
        "frecuencias": [
            {"fuente": "telemetria", "cada": "10 s", "filas": lecturas},
            {"fuente": "clima", "cada": "1 h", "filas": resumen[0]},
            {"fuente": "averias", "cada": "por suceso", "filas": 4},
        ],
        "veces_mas_densa_la_telemetria": round(lecturas / resumen[0]),
        "lecturas_por_hora": 3600 // 10,
        "aceite_meseta_media": float(meseta[0]),
        "aceite_meseta_minimo": float(meseta[1]),
        "aceite_meseta_maximo": float(meseta[2]),
        "horas_cruzadas": correlacion[0],
        "correlacion_calle_aceite": float(correlacion[1]),
        "correlacion_carga_aceite": float(correlacion[2]),
        "grados_del_aceite_por_encima_de_la_calle": float(correlacion[3]),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  {resumen[0]:,} horas de clima, {resumen[1]:,} con temperatura")
    print(f"  de {resumen[2]} a {resumen[3]} grados, media {resumen[4]}")
    print(f"  humedad media {resumen[5]} %")
    print()
    print("  las tres fuentes del lago:")
    for f in payload["frecuencias"]:
        print(f"    {f['fuente']:<12} cada {f['cada']:<12} {f['filas']:>10,} filas")
    print(f"  la telemetría es {payload['veces_mas_densa_la_telemetria']:,} veces más densa "
          f"que el clima")
    print(f"  el 5 de junio, desde las 10:00, el aceite se queda en {meseta[0]} grados "
          f"de media (de {meseta[1]} a {meseta[2]})")
    print()
    print(f"  cruzando {correlacion[0]:,} horas con la plata:")
    print(f"    la calle explica el aceite con correlación {correlacion[1]}")
    print(f"    la carga del compresor, con {correlacion[2]}")
    print(f"    y el aceite va {correlacion[3]} grados por encima de la calle")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if resumen[1] != resumen[0]:
        raise SystemExit(f"El clima trae {resumen[0] - resumen[1]} horas sin temperatura. "
                         "Habría que decidir qué hacer con ellas antes de publicarlo.")


if __name__ == "__main__":
    main()
