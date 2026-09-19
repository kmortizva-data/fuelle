"""Module 29: the whole course as assets that Dagster knows how to build, in order.

An asset is a thing that should exist: a folder of Parquet, a table, a file of
results. Each one declares what it is built from, and from those declarations
Dagster draws the graph, works out the order, runs what is missing, retries what
fails and backfills a stretch of days without touching the rest.

Nothing here computes anything new. Every asset calls a function that already
existed in the course's scripts. The orchestrator's job is the order, not the
arithmetic.

**One rule decides what comes in and what stays out: an asset has to give the
same result every time it runs.** The lesson scripts do two things at once: they
build, and they time what they build with a median of seven runs. A stopwatch
never gives the same number twice, so an orchestrator that ran them would
rewrite the figures the lessons publish on every rebuild. The building comes
here; the timing stays in the lesson scripts, run by hand. Six of them had to be
split for that: bronze.py, silver.py, benchmark_formats.py, table_format.py,
indexes.py and backup.py now expose the building part on its own, and their
main() does exactly what it did before.

Five groups:

    crudo      what nobody here builds: the UCI file, the weather API, the reports
    lago       bronze by day, weather, reports, silver, gold with dbt, Delta and Iceberg
    lecciones  what some lessons query and is not the lake: module 7's single file
    gemelo     physics, simulation, healthy window, calibration, residual, verdict
    servidor   PostgreSQL: the cluster, the load, the schema, the index, the role, the backup

Look at it:   .venv\\Scripts\\python.exe src\\orchestration\\abre.py
Rebuild it:   .venv\\Scripts\\python.exe src\\orchestration\\reconstruye.py
"""

# Sin `from __future__ import annotations` a propósito: Dagster mira el tipo del
# parámetro `context` al cargar, y con esa línea le llegaría como texto.
import shutil
import sys
from pathlib import Path

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DBT_EXE = PROJECT / ".venv" / "Scripts" / "dbt.exe"


def _corre(funcion, *args):
    """Llama a una función de los scripts del curso.

    Los scripts se niegan a seguir con `SystemExit` cuando algo no cuadra, y eso
    es justo lo que tiene que ver el orquestador: se convierte en un fallo del
    activo, con el mismo mensaje, en vez de tumbar el proceso entero.
    """
    try:
        return funcion(*args)
    except SystemExit as e:
        raise dg.Failure(description=str(e.code)) from None


# --- crudo: lo que existe sin que nadie aquí lo construya -------------------
#
#     Se declaran igual para que el grafo empiece donde empieza de verdad. No se
#     pueden materializar: el CSV se baja a mano de la UCI, la API es de otros, y
#     los partes se copiaron de la ficha letra por letra.

CSV = dg.AssetSpec(
    ["crudo", "csv"], group_name="crudo",
    description="MetroPT-3 de la UCI: 1.516.948 lecturas en 208 MB de CSV. Módulo 1.")
OPEN_METEO = dg.AssetSpec(
    ["crudo", "open_meteo"], group_name="crudo",
    description="La API de clima histórico de Open-Meteo. La única pieza que depende de la red.")
PARTES = dg.AssetSpec(
    ["crudo", "partes"], group_name="crudo",
    description="Los cuatro partes de avería, copiados de la ficha con sus erratas. Módulo 1.")


# --- lago -------------------------------------------------------------------

# Del 1 de febrero al 1 de septiembre de 2020, ambos incluidos. Son 214 días de
# calendario y el registro trae 212: al 29 de febrero y al 26 de abril no les
# llegó ni una lectura (módulo 8). El orquestador conoce el calendario; el dato,
# no. Esos dos días se materializan igual, vacíos.
DIAS = dg.DailyPartitionsDefinition(start_date="2020-02-01", end_date="2020-09-02")


@dg.asset(key=["lago", "bronce"], deps=[CSV], group_name="lago",
          partitions_def=DIAS, backfill_policy=dg.BackfillPolicy.single_run(),
          description="El CSV tal cual, en Parquet y con una carpeta por día. Módulos 4 a 6.")
def bronce(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    import duckdb
    from ingest import bronze

    # Un tramo de días en una sola corrida, sea el registro entero o un día
    # suelto. Es lo que se llama rellenar hacia atrás: se rehace ese tramo y el
    # resto del lago ni se entera.
    tramo = context.partition_key_range
    dias = (tramo.start, tramo.end)
    bronze.clear(dias)
    con = duckdb.connect()
    bronze.write(con, dias)
    lecturas = con.sql(f"""
        SELECT count(*) FROM read_parquet('{bronze.BRONZE.as_posix()}/**/*.parquet')
        WHERE day BETWEEN DATE '{dias[0]}' AND DATE '{dias[1]}'
    """).fetchone()[0]
    bronze.write_manifest(bronze.fingerprint(bronze.RAW_CSV), bronze.inventory(con))
    con.close()
    return dg.MaterializeResult(metadata={"desde": dias[0], "hasta": dias[1],
                                          "lecturas": lecturas})


@dg.asset(key=["lago", "clima"], deps=[OPEN_METEO], group_name="lago",
          retry_policy=dg.RetryPolicy(max_retries=3, delay=10,
                                      backoff=dg.Backoff.EXPONENTIAL),
          description="El tiempo en Oporto hora a hora. Se baja una vez y se guarda. Módulo 15.")
def clima() -> dg.MaterializeResult:
    # La única pieza que habla con la red, y por eso la única con reintentos:
    # tres más, esperando 10, 20 y 40 segundos. Si Open-Meteo no contesta a la
    # primera, lo normal es que conteste a la segunda, y un orquestador que se
    # rinde al primer fallo de la red despierta a alguien a las tres de la mañana.
    #
    # Solo `construye()`: bajar y escribir el bronce. El `main()` del módulo 15
    # cruza además el clima con la plata, y la primera reconstrucción lo corrió
    # antes de que la plata existiera: escribió null en siete cifras publicadas.
    from ingest import weather

    return dg.MaterializeResult(metadata=_corre(weather.construye))


@dg.asset(key=["lago", "averias"], deps=[PARTES], group_name="lago",
          description="Los partes de avería en Parquet, con sus erratas intactas. Módulo 15.")
def averias() -> None:
    from ingest import failures

    _corre(failures.main)


@dg.asset(key=["lago", "plata"], deps=[bronce], group_name="lago",
          description="La telemetría en rejilla de 10 s, con los huecos a la vista. Módulo 14.")
def plata() -> dg.MaterializeResult:
    from transform import silver

    hecho = _corre(silver.construye)
    return dg.MaterializeResult(metadata=hecho)


@dg.asset_check(asset=plata, description="Las ocho promesas del contrato del módulo 16.")
def el_contrato_se_cumple() -> dg.AssetCheckResult:
    import duckdb
    from transform import contracts

    con = duckdb.connect()
    con.execute(f"CREATE VIEW datos AS SELECT * FROM "
                f"read_parquet('{contracts.SILVER.as_posix()}/**/*.parquet')")
    promesas = {**contracts.CONTRATO, **contracts.PROMESA_QUE_FALTABA}
    rotas = contracts.revisa(con, promesas)
    con.close()
    return dg.AssetCheckResult(
        passed=not rotas,
        metadata={"promesas": len(promesas), "rotas": len(rotas),
                  "cuales": "; ".join(f"{p}: {por_que}" for p, por_que in rotas) or "ninguna"})


# El oro lo construye dbt, y aquí no se reescribe ni una línea de él: Dagster
# lee el manifest del módulo 17 y convierte cada modelo en un activo y cada
# prueba de dbt en una comprobación. Las fuentes de dbt se llaman `lago.plata`,
# `lago.clima` y `lago.averias`, así que caen solas sobre los activos de
# arriba, que tienen esas mismas claves.
DBT = DbtProject(project_dir=PROJECT / "dbt", profiles_dir=PROJECT / "dbt")
if not DBT.manifest_path.exists():
    # El manifest no se versiona. En una máquina recién clonada hay que pedirle
    # a dbt que lo escriba antes de que Dagster pueda leerlo.
    DBT.preparer.prepare(DBT)


class _AlLago(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props) -> str:
        return "lago"


@dbt_assets(manifest=DBT.manifest_path, project=DBT, dagster_dbt_translator=_AlLago())
def oro(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    # dbt abre su base en `lake/gold/` y no crea la carpeta: en un lago recién
    # borrado no existe todavía.
    (PROJECT / "lake" / "gold").mkdir(parents=True, exist_ok=True)
    yield from dbt.cli(["build"], context=context).stream()


@dg.asset(key=["lago", "historia"], deps=[bronce, plata], group_name="lago",
          description="El oro diario en Delta y en Iceberg, con la versión del fallo "
                      "y la arreglada. Módulo 18.")
def historia() -> dg.MaterializeResult:
    from transform import table_format

    return dg.MaterializeResult(metadata=_corre(table_format.construye))


# --- lecciones: lo que alguna lección consulta y no es el lago --------------

@dg.asset(key=["lecciones", "todo_en_un_parquet"], deps=[bronce], group_name="lecciones",
          description="El registro entero en un solo Parquet, que consultan las lecciones "
                      "del módulo 7.")
def todo_en_un_parquet() -> None:
    import duckdb
    from transform import benchmark_formats

    con = duckdb.connect()
    benchmark_formats.write_whole_file(con)
    con.close()


# --- gemelo -----------------------------------------------------------------
#
#     Cada paso del gemelo ya era un script que escribe sus resultados medidos y
#     se niega a publicar si no cuadran. Aquí se ejecutan tal cual: ninguno
#     cronometra nada, así que dan los mismos bytes cada vez.

def _gemelo(clave: str, deps: list, modulo: str, que: str) -> dg.AssetsDefinition:
    @dg.asset(key=["gemelo", clave], deps=deps, group_name="gemelo", description=que)
    def _paso() -> None:
        import importlib

        _corre(importlib.import_module(modulo).main)

    return _paso


fisica = _gemelo("fisica", [plata], "twin.model",
                 "Los cuatro números del gemelo, medidos del lago. Módulo 24.")
simulacion = _gemelo("simulacion", [fisica], "twin.simulate",
                     "El gemelo en marcha, y las series de tres perillas. Módulo 25.")
ventana_sana = _gemelo("ventana_sana", [plata], "twin.ventana_sana",
                       "La prueba de que febrero es una máquina en un solo estado. Módulo 26.")
calibracion = _gemelo("calibracion", [fisica, ventana_sana], "twin.calibrate",
                      "Los parámetros buscados por ajuste, contra los medidos. Módulo 26.")
residual = _gemelo("residual", [fisica, PARTES], "twin.residual",
                   "El residual hora a hora, sus dos rutas y la perilla de la fuga. Módulo 27.")
veredicto = _gemelo("veredicto", [residual, PARTES], "twin.evaluate",
                    "Las cuatro averías contra el gemelo y contra la alarma instalada. Módulo 28.")


# --- servidor ---------------------------------------------------------------
#
#     PostgreSQL va aparte porque su gigabyte no debe comerse la cifra del lago.
#     Cada paso arranca el servidor si hace falta y lo para al terminar, con el
#     `servidor()` del módulo 19, que solo para lo que arrancó él.

@dg.asset(key=["servidor", "cluster"], group_name="servidor",
          description="El directorio de datos de PostgreSQL, con initdb y las tres líneas "
                      "que cambia el curso. Módulo 19.")
def cluster() -> dg.MaterializeResult:
    from db import servidor

    creado = _corre(servidor.crea_cluster)
    return dg.MaterializeResult(metadata={"creado_ahora": creado})


@dg.asset(key=["servidor", "lecturas"], deps=[plata, cluster], group_name="servidor",
          description="La plata cargada en el servidor con COPY. Módulo 19.")
def lecturas() -> dg.MaterializeResult:
    from db import load_silver
    from db.servidor import conecta, servidor

    filas = load_silver.exporta_csv()
    with servidor():
        pg = conecta()
        load_silver.crea_tabla(pg)
        load_silver.carga(pg)
        en_servidor = pg.execute("SELECT count(*) FROM lecturas").fetchone()[0]
        pg.close()
    # El CSV era un intermedio de 190 MB y no tiene por qué quedarse.
    shutil.rmtree(load_silver.TRABAJO, ignore_errors=True)
    if en_servidor != filas:
        raise dg.Failure(description=f"El servidor tiene {en_servidor:,} filas y la "
                                     f"plata {filas:,}. La carga ha perdido filas.")
    return dg.MaterializeResult(metadata={"filas": en_servidor})


@dg.asset(key=["servidor", "esquema"], deps=[lecturas], group_name="servidor",
          description="Claves, restricciones y la tabla de días. Módulo 20.")
def esquema() -> dg.MaterializeResult:
    from db import schema
    from db.servidor import conecta, servidor

    with servidor():
        pg = conecta()
        hecho = _corre(schema.construye, pg)
        hecho.pop("psycopg")
        pg.close()
    return dg.MaterializeResult(metadata=hecho)


@dg.asset(key=["servidor", "indice"], deps=[esquema], group_name="servidor",
          description="El índice por día de la tabla de lecturas. Módulo 21.")
def indice() -> None:
    from db import indexes
    from db.servidor import conecta, servidor

    with servidor():
        pg = conecta()
        indexes.crea_indice(pg)
        pg.close()


@dg.asset(key=["servidor", "rol_de_lectura"], deps=[esquema], group_name="servidor",
          description="Un rol que puede leer y no puede escribir, comprobado. Módulo 22.")
def rol_de_lectura() -> dg.MaterializeResult:
    from db import backup
    from db.servidor import conecta, servidor

    with servidor():
        pg = conecta(autocommit=True)
        rol = backup.prueba_el_rol(pg)
        pg.close()
    if rol["puede_escribir"]:
        raise dg.Failure(description="El rol de solo lectura ha podido borrar.")
    return dg.MaterializeResult(metadata={"lee": rol["lee"], "error_al_borrar": rol["error"]})


@dg.asset(key=["servidor", "copia"], deps=[indice, rol_de_lectura], group_name="servidor",
          description="La base entera en una copia de pg_dump. Módulo 22.")
def copia() -> dg.MaterializeResult:
    from db import backup
    from db.servidor import servidor

    with servidor():
        mb = _corre(backup.copia)
    return dg.MaterializeResult(metadata={"mb": round(mb, 1)})


@dg.asset_check(asset=copia, description="La copia se restaura en otra base y sale igual.")
def la_copia_restaura() -> dg.AssetCheckResult:
    # Una copia que nadie ha restaurado no es una copia: es el título del módulo
    # 22. El orquestador no la da por buena hasta hacer eso mismo.
    from db import backup
    from db.servidor import conecta, servidor

    with servidor():
        pg = conecta(autocommit=True)
        hecho = backup.la_copia_restaura(pg)
        pg.close()
    return dg.AssetCheckResult(
        passed=hecho["iguales"],
        metadata={"guardas": hecho["guardas"], "guardas_restauradas": hecho["guardas_restauradas"],
                  "lecturas": ", ".join(hecho["huellas"]["lecturas"])})


defs = dg.Definitions(
    assets=[CSV, OPEN_METEO, PARTES,
            bronce, clima, averias, plata, oro, historia,
            todo_en_un_parquet,
            fisica, simulacion, ventana_sana, calibracion, residual, veredicto,
            cluster, lecturas, esquema, indice, rol_de_lectura, copia],
    asset_checks=[el_contrato_se_cumple, la_copia_restaura],
    resources={"dbt": DbtCliResource(project_dir=DBT, dbt_executable=str(DBT_EXE))},
)
