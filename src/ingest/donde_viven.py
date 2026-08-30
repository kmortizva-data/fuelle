"""La misma pregunta, cuatro sitios donde vivir. Módulo 3.

«Fichero», «base de datos», «lago» y «almacén» se usan como si fueran sinónimos
y no lo son. La diferencia no se explica bien con palabras, pero se ve entera
cronometrando la misma pregunta en cada uno.

La pregunta es la misma siempre y de las más sencillas que hay: cuántas lecturas
hay de un día concreto. Lo único que cambia es dónde están los datos.

Se mide el tamaño en disco, el tiempo de la primera consulta (que incluye abrir
y entender el fichero) y el de la segunda (con el sistema ya caliente), porque
esa diferencia también es parte de la respuesta.

Correr:  .venv\\Scripts\\python.exe src\\ingest\\donde_viven.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import time
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_donde"
RESULTS = PROJECT / "results" / "m03_donde_viven.json"

DIA = "2020-06-05"


def tamaño(path: Path) -> float:
    if path.is_dir():
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024
    return path.stat().st_size / 1024 / 1024


REPETICIONES = 7


def cronometrar(con, sql: str) -> tuple[float, float, float, int]:
    """La mediana de siete corridas, con su rango.

    Una sola medida no es una medida. La primera versión de este script
    cronometraba una vez, y dos ejecuciones seguidas dieron 203,7 y 143,8 veces
    entre los extremos: la conclusión aguantaba, pero el número publicado no.
    A escala de milisegundos manda lo que la máquina esté haciendo por su cuenta.

    Se devuelve la mediana porque un pico aislado no debe mover el resultado, y
    también el mínimo y el máximo, porque esconder la variabilidad sería fingir
    una precisión que no hay.
    """
    tiempos = []
    filas = 0
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        filas = con.sql(sql).fetchone()[0]
        tiempos.append(time.perf_counter() - inicio)
    tiempos.sort()
    return tiempos[len(tiempos) // 2], tiempos[0], tiempos[-1], filas


def main() -> None:
    if not CSV.exists() or not BRONZE.exists():
        raise SystemExit("Faltan los datos. Corre src/ingest/bronze.py primero.")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    medidas = []

    # 1. Un fichero de texto suelto. Hay que leerlo entero para contestar.
    con = duckdb.connect()
    sql = (f"SELECT count(*) FROM read_csv_auto('{CSV.as_posix()}') "
           f"WHERE CAST(timestamp AS DATE) = DATE '{DIA}'")
    mediana, minimo, maximo, filas = cronometrar(con, sql)
    medidas.append({"sitio": "un fichero de texto", "formato": "CSV",
                    "mb": round(tamaño(CSV), 2), "mediana_s": round(mediana, 3),
                    "min_s": round(minimo, 3), "max_s": round(maximo, 3), "filas": filas})
    con.close()

    # 2. El mismo dato en formato columnar, repartido en carpetas por día.
    con = duckdb.connect()
    sql = (f"SELECT count(*) FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet') "
           f"WHERE CAST(timestamp AS DATE) = DATE '{DIA}'")
    mediana, minimo, maximo, filas = cronometrar(con, sql)
    medidas.append({"sitio": "un lago de ficheros", "formato": "Parquet particionado",
                    "mb": round(tamaño(BRONZE), 2), "mediana_s": round(mediana, 3),
                    "min_s": round(minimo, 3), "max_s": round(maximo, 3), "filas": filas})
    con.close()

    # 3. Una base de datos de verdad: los datos dentro, con su propio formato.
    db = SCRATCH / "compresor.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    con.execute(
        f"CREATE TABLE telemetria AS "
        f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
    )
    con.close()
    con = duckdb.connect(str(db))
    sql = f"SELECT count(*) FROM telemetria WHERE CAST(timestamp AS DATE) = DATE '{DIA}'"
    mediana, minimo, maximo, filas = cronometrar(con, sql)
    medidas.append({"sitio": "una base de datos", "formato": "DuckDB",
                    "mb": round(tamaño(db), 2), "mediana_s": round(mediana, 3),
                    "min_s": round(minimo, 3), "max_s": round(maximo, 3), "filas": filas})

    # 4. La misma base con la columna del día ya calculada e indexada: es lo que
    #    hace un almacén, preparar el dato para las preguntas que se repiten.
    #
    #    En su PROPIO fichero, y no junto a la tabla anterior. La primera versión
    #    de este script las metía en el mismo, así que el tamaño del almacén
    #    incluía la tabla de al lado y salía el doble de grande. Un número que
    #    engaña sin querer sigue engañando.
    almacen = SCRATCH / "almacen.duckdb"
    almacen.unlink(missing_ok=True)
    con2 = duckdb.connect(str(almacen))
    con2.execute(
        f"CREATE TABLE almacen AS SELECT *, CAST(timestamp AS DATE) AS dia "
        f"FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
    )
    con2.execute("CREATE INDEX idx_dia ON almacen(dia)")
    con2.close()
    con2 = duckdb.connect(str(almacen))
    sql = f"SELECT count(*) FROM almacen WHERE dia = DATE '{DIA}'"
    mediana, minimo, maximo, filas = cronometrar(con2, sql)
    medidas.append({"sitio": "un almacén", "formato": "DuckDB con índice",
                    "mb": round(tamaño(almacen), 2), "mediana_s": round(mediana, 3),
                    "min_s": round(minimo, 3), "max_s": round(maximo, 3), "filas": filas})
    con2.close()

    print(f"  mediana de {REPETICIONES} corridas por sitio")
    print("  sitio                 formato                 tamaño  mediana     min     max")
    for m in medidas:
        print(f"  {m['sitio']:<21} {m['formato']:<22} {m['mb']:>7.2f} MB "
              f"{m['mediana_s']:>7.3f} {m['min_s']:>7.3f} {m['max_s']:>7.3f}")

    coinciden = len({m["filas"] for m in medidas}) == 1
    lento = max(medidas, key=lambda m: m["mediana_s"])
    rapido = min(medidas, key=lambda m: m["mediana_s"])
    veces = lento["mediana_s"] / rapido["mediana_s"]

    resultados = {"dia": DIA, "sitios": medidas, "todos_coinciden": coinciden,
                  "filas_ese_dia": medidas[0]["filas"],
                  "repeticiones": REPETICIONES,
                  "veces_entre_extremos": round(veces, 1),
                  # El redondeo a entero se guarda aquí en vez de hacerse al
                  # escribir la lección: así el número que se publica sale de una
                  # corrida igual que los demás, y no de la mano de nadie.
                  "veces_redondeadas": round(veces),
                  "mas_lento": lento["sitio"], "mas_rapido": rapido["sitio"],
                  # Lo que cuesta el índice, calculado aquí y no a mano al
                  # escribir la lección: un número derivado también es un número.
                  "mb_de_mas_del_indice": round(
                      medidas[3]["mb"] - medidas[2]["mb"], 1),
                  "veces_indice_mas_lento": round(
                      medidas[3]["mediana_s"] / medidas[2]["mediana_s"], 2)}
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(resultados, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  los cuatro devuelven {medidas[0]['filas']:,} filas del {DIA}: {coinciden}")
    print(f"  del más lento al más rápido: {veces:.1f} veces")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    shutil.rmtree(SCRATCH, ignore_errors=True)

    if not coinciden:
        raise SystemExit("Los cuatro sitios no dan la misma respuesta. La comparación no vale.")


if __name__ == "__main__":
    main()
