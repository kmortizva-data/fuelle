"""Two open table formats, the same table, and this project's own bug. Module 18.

A plain Parquet directory forgets. Overwrite it and yesterday is gone, so the
question "what did the panel say before we found the bug" has no answer.

An open table format keeps the old files and writes a log of what each version
contained, which turns that question into a query. There are two serious ones
that run without Spark, so instead of picking by reputation this module builds
BOTH and measures, the way module 6 measured partition layouts.

The version history is not invented. It is the real failure of this project's
silver layer: the first version of `silver.py` joined readings to the ten second
grid on an exact timestamp match and kept 151,657 of 1,516,948, one in ten,
because this clock walks. So the gold table gets written twice in each format:

  - version 0: the daily cycle computed from the buggy silver
  - version 1: the same table from the fixed silver

What is measured, with `medir.measure` and its median of seven:

  - bytes on disk and files created, once both versions are in
  - writing a version, which is paid on every pipeline run
  - reading the latest version, the normal case
  - reading the old version, which is the thing being bought
  - what each format needs before it will work at all

And module 6's rule applies unchanged: when two ranges overlap there is no
difference to report. `distinguishable()` decides, not the medians.

Run:  .venv\\Scripts\\python.exe src\\transform\\table_format.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import time
from pathlib import Path

import duckdb
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import distinguishable, measure, times_slower  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
FORMATS = PROJECT / "lake" / "_formatos_de_tabla"
DELTA = FORMATS / "delta"
ICEBERG = FORMATS / "iceberg"
CATALOGO = FORMATS / "catalogo.db"
# Los dos punteros que este proyecto mantiene A MANO para poder publicar una
# consulta de Iceberg que se pueda copiar. Su nombre de verdad lleva un uuid que
# cambia en cada corrida, y quien sabe cual es el bueno es el catalogo, no la
# carpeta. Delta no necesita nada de esto: se le apunta a la carpeta y ya.
PUNTERO_ULTIMA = FORMATS / "iceberg_ultima.metadata.json"
PUNTERO_PRIMERA = FORMATS / "iceberg_primera.metadata.json"
SAMPLES = PROJECT / "assets" / "muestras"
RESULTS = PROJECT / "results" / "m18_formatos.json"

PASO = 10  # los segundos de la rejilla, como en silver.py

# El agregado diario, escrito una sola vez y calculado sobre dos plata distintas.
# Es la forma de `oro_ciclo_diario` del modulo 17, recortada a lo que la lección
# necesita comparar.
CICLO = """
    SELECT day                                                        AS dia,
           count(*)                                                   AS lecturas,
           round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                 * {paso} / 3600.0, 2)                                AS horas_de_carga,
           round(avg(Oil_temperature), 2)                             AS aceite_medio
    FROM {plata}
    GROUP BY day
    ORDER BY day
"""

# La plata con el fallo: cruzar la rejilla por marca de tiempo EXACTA. No hace
# falta guardar la version vieja del script, porque el fallo cabe en un JOIN.
PLATA_CON_EL_FALLO = """
    (
        WITH rejilla AS (
            SELECT unnest(generate_series(TIMESTAMP '{desde}', TIMESTAMP '{hasta}',
                                          INTERVAL {paso} SECOND)) AS timestamp
        )
        SELECT b.* FROM rejilla r JOIN bronce b ON b.timestamp = r.timestamp
    )
"""


def bytes_y_ficheros(carpeta: Path) -> tuple[int, int]:
    ficheros = [f for f in carpeta.rglob("*") if f.is_file()]
    return sum(f.stat().st_size for f in ficheros), len(ficheros)


def conecta_con_extensiones() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for ext in ("delta", "iceberg"):
        con.execute(f"INSTALL {ext}")
        con.execute(f"LOAD {ext}")
    # Iceberg no dice en su carpeta cual es la version buena: eso lo sabe el
    # catalogo. DuckDB se niega a adivinarlo mirando los ficheros, con razon,
    # porque podria leer algo a medio escribir. Delta no necesita esto: su
    # registro vive dentro de la propia carpeta de la tabla.
    con.execute("SET unsafe_enable_version_guessing = true")
    return con


_CATALOGO_ABIERTO = None


def catalogo_iceberg():
    """Iceberg needs a catalog before it can hold a single row.

    That is the first measured difference between the two, and it needs no
    stopwatch: Delta writes into an empty directory, Iceberg wants somebody to
    keep the list of tables. The cheapest one that works without a server is
    SQLite in a file, and that file is the whole setup cost.
    """
    from pyiceberg.catalog.sql import SqlCatalog

    # Se guarda uno solo y se reutiliza. Abrir un catalogo nuevo en cada corrida
    # deja el SQLite abierto, y en Windows un fichero abierto no se puede borrar:
    # la medicion de escritura reventaba al limpiar entre repeticiones.
    global _CATALOGO_ABIERTO
    if _CATALOGO_ABIERTO is not None:
        return _CATALOGO_ABIERTO

    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    # El almacen va SIN esquema `file://`. Con el, pyiceberg escribe rutas
    # `file://C:/...` dentro del metadato y DuckDB no las sabe abrir en Windows:
    # falla al buscar el manifiesto, no la tabla. Costo un rato encontrarlo.
    _CATALOGO_ABIERTO = SqlCatalog(
        "fuelle",
        **{"uri": f"sqlite:///{CATALOGO.as_posix()}",
           "warehouse": ICEBERG.as_posix()},
    )
    return _CATALOGO_ABIERTO


def apunta_al_metadato() -> None:
    """Copia los dos metadatos que la lección consulta a un nombre estable.

    Es un apaño, y la lección lo dice tal cual. Existe porque el fichero de
    metadatos de Iceberg se llama `00002-<uuid>.metadata.json` y ese uuid cambia
    en cada corrida, así que una consulta publicada apuntando a él dejaría de
    funcionar mañana. Delta no obliga a nada parecido.
    """
    metadatos = sorted((ICEBERG / "oro" / "ciclo_diario" / "metadata")
                       .glob("*.metadata.json"))
    # El 00000 es la tabla recién creada y vacía; el 00001 trae la versión con el
    # fallo y el 00002 la arreglada.
    shutil.copyfile(metadatos[1], PUNTERO_PRIMERA)
    shutil.copyfile(metadatos[-1], PUNTERO_ULTIMA)


def main() -> None:
    if not (BRONZE.exists() and SILVER.exists()):
        raise SystemExit("Faltan bronce o plata. Corre src/ingest/bronze.py y "
                         "src/transform/silver.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW bronce AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    con.execute(f"CREATE VIEW plata AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")

    borde = con.sql("SELECT min(timestamp), max(timestamp) FROM bronce").fetchone()
    con_el_fallo = PLATA_CON_EL_FALLO.format(desde=borde[0], hasta=borde[1], paso=PASO)

    lecturas_del_fallo = con.sql(
        f"SELECT count(*) FROM {con_el_fallo}").fetchone()[0]
    lecturas_de_verdad = con.sql("SELECT count(*) FROM bronce").fetchone()[0]

    # `.arrow()` devuelve un lector de un solo uso, y aqui las dos tablas se
    # escriben siete veces cada una: hay que materializarlas.
    v0 = con.sql(CICLO.format(plata=con_el_fallo, paso=PASO)).arrow().read_all()
    v1 = con.sql(CICLO.format(plata="plata WHERE medido", paso=PASO)).arrow().read_all()

    print(f"  version 0, con el fallo:  {v0.num_rows:>3} dias, "
          f"{lecturas_del_fallo:>9,} lecturas")
    print(f"  version 1, arreglada:     {v1.num_rows:>3} dias, "
          f"{lecturas_de_verdad:>9,} lecturas")

    # Lo que el panel decia antes y despues, que es la pregunta del modulo.
    def media_de_carga(tabla: pa.Table) -> float:
        d = duckdb.connect()
        d.register("t", tabla)
        return d.sql("SELECT round(avg(horas_de_carga), 2) FROM t").fetchone()[0]

    carga_v0, carga_v1 = media_de_carga(v0), media_de_carga(v1)
    print(f"  el panel decia {carga_v0} h de carga al dia, y son {carga_v1}")

    # --- Delta -----------------------------------------------------------
    from deltalake import DeltaTable, write_deltalake
    from pyiceberg.exceptions import NoSuchTableError

    def escribe_delta() -> None:
        write_deltalake(str(DELTA), v0, mode="overwrite")
        write_deltalake(str(DELTA), v1, mode="overwrite")

    def limpia_delta() -> None:
        shutil.rmtree(DELTA, ignore_errors=True)

    t0 = time.perf_counter()
    limpia_delta()
    escribe_delta()
    montar_delta = time.perf_counter() - t0

    # --- Iceberg ---------------------------------------------------------
    def escribe_iceberg() -> None:
        cat = catalogo_iceberg()
        cat.create_namespace_if_not_exists("oro")
        try:
            cat.drop_table("oro.ciclo_diario")
        except NoSuchTableError:
            pass
        tabla = cat.create_table("oro.ciclo_diario", schema=v0.schema)
        tabla.append(v0)
        tabla.overwrite(v1)

    def limpia_iceberg() -> None:
        cat = catalogo_iceberg()
        try:
            cat.drop_table("oro.ciclo_diario")
        except NoSuchTableError:
            pass
        shutil.rmtree(ICEBERG, ignore_errors=True)
        ICEBERG.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    limpia_iceberg()
    ICEBERG.mkdir(parents=True, exist_ok=True)
    escribe_iceberg()
    montar_iceberg = time.perf_counter() - t0

    # --- Lo que ocupan ---------------------------------------------------
    bytes_delta, ficheros_delta = bytes_y_ficheros(DELTA)
    bytes_iceberg, ficheros_iceberg = bytes_y_ficheros(ICEBERG)
    bytes_iceberg += CATALOGO.stat().st_size
    ficheros_iceberg += 1  # el catálogo cuenta: sin él la tabla no se encuentra

    # --- Leer, con DuckDB y con las extensiones --------------------------
    #
    #     Las cuatro lecturas van por DuckDB y por las extensiones, para que la
    #     comparación sea de verdad la misma pregunta hecha dos veces.
    apunta_al_metadato()
    d = conecta_con_extensiones()
    CUENTA = "SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas FROM"

    def lee_delta_ultima():
        return d.sql(f"{CUENTA} delta_scan('{DELTA.as_posix()}')").fetchall()

    def lee_delta_vieja():
        return d.sql(f"{CUENTA} delta_scan('{DELTA.as_posix()}', version = 0)").fetchall()

    def lee_iceberg_ultima():
        return d.sql(f"{CUENTA} iceberg_scan('{PUNTERO_ULTIMA.as_posix()}')").fetchall()

    def lee_iceberg_vieja():
        return d.sql(f"{CUENTA} iceberg_scan('{PUNTERO_PRIMERA.as_posix()}')").fetchall()

    def lee_iceberg_por_el_catalogo():
        """Lo mismo, pero preguntando primero cual es la version buena.

        Las dos lecturas de arriba parten de un puntero que ya sabemos donde
        esta, asi que se saltan el paso que una consulta de verdad no se puede
        saltar. Esta lo paga, y la diferencia entre las dos es lo que cuesta el
        catalogo. Sin medirla, la comparacion estaria hecha a favor de Iceberg.
        """
        loc = catalogo_iceberg().load_table("oro.ciclo_diario").metadata_location
        return d.sql(f"{CUENTA} iceberg_scan('{loc}')").fetchall()

    print()
    print(f"  delta   la ultima {lee_delta_ultima()}   la vieja {lee_delta_vieja()}")
    print(f"  iceberg la ultima {lee_iceberg_ultima()}   la vieja {lee_iceberg_vieja()}")

    versiones_delta = len(DeltaTable(str(DELTA)).history())
    metadatos_iceberg = len(sorted((ICEBERG / "oro" / "ciclo_diario" / "metadata")
                                   .glob("*.metadata.json")))
    print(f"  delta guarda {versiones_delta} versiones; iceberg deja "
          f"{metadatos_iceberg} metadatos, y el primero es la tabla vacia")

    # --- Las medidas, mediana de siete -----------------------------------
    print()
    print("  midiendo, mediana de siete:")
    medidas = {"escribir las dos versiones": {
        "delta": measure(escribe_delta, setup=limpia_delta),
        "iceberg": measure(escribe_iceberg, setup=limpia_iceberg),
    }}
    # Medir la escritura ha vuelto a escribir las dos tablas, asi que los
    # punteros del apano apuntan a ficheros que ya no existen. Se rehacen antes
    # de medir las lecturas, o se mide un error.
    apunta_al_metadato()
    medidas["leer la última versión"] = {
        "delta": measure(lee_delta_ultima),
        "iceberg": measure(lee_iceberg_ultima),
    }
    medidas["leer la versión vieja"] = {
        "delta": measure(lee_delta_vieja),
        "iceberg": measure(lee_iceberg_vieja),
    }
    medidas["leer preguntando primero"] = {
        "delta": measure(lee_delta_ultima),
        "iceberg": measure(lee_iceberg_por_el_catalogo),
    }

    comparacion = {}
    for que, par in medidas.items():
        a, b = par["delta"], par["iceberg"]
        se_distinguen = distinguishable(a, b)
        rapido = "delta" if a.median <= b.median else "iceberg"
        factor = times_slower(b, a) if rapido == "delta" else times_slower(a, b)
        comparacion[que] = {
            "delta": {"mediana": round(a.median, 4), "minimo": round(a.minimum, 4),
                      "maximo": round(a.maximum, 4)},
            "iceberg": {"mediana": round(b.median, 4), "minimo": round(b.minimum, 4),
                        "maximo": round(b.maximum, 4)},
            "se_distinguen": se_distinguen,
            "mas_rapido": rapido if se_distinguen else None,
            "veces": round(factor, 1) if factor else None,
        }
        veredicto = (f"{rapido} va {factor:.1f} veces mas rapido"
                     if se_distinguen and factor else "no se distinguen")
        print(f"    {que:<28} delta {a.median:.4f} s   iceberg {b.median:.4f} s   "
              f"{veredicto}")

    payload = {
        "lecturas_con_el_fallo": lecturas_del_fallo,
        "lecturas_de_verdad": lecturas_de_verdad,
        "dias_en_la_version_0": v0.num_rows,
        "dias_en_la_version_1": v1.num_rows,
        "horas_de_carga_que_decia_la_version_0": carga_v0,
        "horas_de_carga_de_verdad": carga_v1,
        "versiones_que_guarda_delta": versiones_delta,
        # El tamaño sí es estable entre corridas, al contrario que los tiempos,
        # así que este factor se puede citar en la prosa sin que caduque.
        "veces_mas_disco_iceberg": round(bytes_iceberg / bytes_delta, 1),
        "metadatos_que_deja_iceberg": metadatos_iceberg,
        "delta": {
            "kb_en_disco": round(bytes_delta / 1024, 1),
            "ficheros": ficheros_delta,
            "montaje": "nada: se escribe en una carpeta vacia",
            "segundos_de_montaje": round(montar_delta, 3),
        },
        "iceberg": {
            "kb_en_disco": round(bytes_iceberg / 1024, 1),
            "ficheros": ficheros_iceberg,
            "montaje": "un catalogo SQLite que guarda donde esta cada tabla",
            "segundos_de_montaje": round(montar_iceberg, 3),
        },
        "medidas": comparacion,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  delta    {bytes_delta / 1024:>8.1f} KB en {ficheros_delta:>2} ficheros, "
          f"sin nada que montar")
    print(f"  iceberg  {bytes_iceberg / 1024:>8.1f} KB en {ficheros_iceberg:>2} ficheros, "
          f"con un catalogo SQLite")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
