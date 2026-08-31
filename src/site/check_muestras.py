"""Lo que el lector ejecuta es la muestra, no el lago. Esta puerta mira ahí.

`check_sql.py` ejecuta cada consulta publicada contra el lago, y eso deja un
hueco del tamaño de un módulo: **el navegador no tiene el lago**. Tiene una
muestra con menos columnas, y desde la parte 3 cada módulo se baja una distinta.

Una consulta que usa `TP3` corre perfectamente contra el lago y revienta en el
navegador si la muestra de ese módulo no lleva `TP3`. `check_sql` daría verde y
el lector vería un error. Esa es exactamente la clase de fallo que este curso no
se puede permitir, porque su argumento entero es que las consultas se ejecutan
de verdad.

Esta puerta comprueba cuatro cosas:

  1. Que el fichero de cada muestra declarada en `temario.json` existe.
  2. Que **cada consulta viva y cada reto corre contra la muestra de SU módulo**,
     no contra el lago.
  3. Que da **el mismo resultado** en la muestra y en el lago, cuando la muestra
     lleva todas las filas. Si difieren, el lector acierta y la página le dice
     que no.
  4. Que ninguna muestra se publica sin que la use alguien.

El punto 3 se salta en las muestras que llevan un subconjunto de filas, como la
de un día del módulo 13, y a cambio se exige que todas sus consultas filtren por
ese día. Sin ese filtro, la consulta diría una cosa en la página y otra en el
lago.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_muestras.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_sql import bloques, normaliza  # noqa: E402
from make_sample import POR_HORA  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
LESSONS = PROJECT / "lecciones"
SAMPLES = PROJECT / "assets" / "muestras"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
WEATHER = PROJECT / "lake" / "bronze" / "weather"
TEMARIO = PROJECT / "temario.json"
SAMPLE_FACTS = PROJECT / "results" / "sample.json"

POR_DEFECTO = "sin_timestamp_ligera"


def declared(module: dict) -> dict[str, str]:
    """Las vistas que la página de ese módulo va a registrar."""
    if module.get("tablas"):
        return dict(module["tablas"])
    tablas = {"telemetria": module.get("muestra", POR_DEFECTO)}
    for extra in module.get("tablas_extra", []):
        tablas[extra] = extra
    return tablas


def connect_sample(tablas: dict[str, str]) -> duckdb.DuckDBPyConnection:
    """Un motor con exactamente lo que tendrá el navegador. Ni una tabla más."""
    con = duckdb.connect()
    for view, fichero in tablas.items():
        path = SAMPLES / f"{fichero}.parquet"
        con.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{path.as_posix()}')")
    return con


def connect_lake(tablas: dict[str, str]) -> duckdb.DuckDBPyConnection:
    """El mismo juego de vistas, pero construidas desde el lago.

    Las tablas derivadas, como las horarias del módulo 15, se rehacen aquí con
    la misma consulta que las generó. Leerlas del propio fichero de muestra
    haría que la comparación se hiciera consigo misma y no comprobara nada.
    """
    con = duckdb.connect()
    con.execute(f"CREATE VIEW telemetria AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    for view, fichero in tablas.items():
        if view == "telemetria":
            continue
        if fichero in POR_HORA and WEATHER.exists() and SILVER.exists():
            sql = POR_HORA[fichero].format(weather=WEATHER.as_posix(),
                                           silver=SILVER.as_posix())
            con.execute(f"CREATE VIEW {view} AS {sql}")
        else:
            path = SAMPLES / f"{fichero}.parquet"
            con.execute(
                f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{path.as_posix()}')")
    return con


def queries_of(path: Path) -> list[tuple[int, str]]:
    """Toda consulta que el lector puede llegar a ejecutar en esa página."""
    text = io.open(path, encoding="utf-8").read()
    out = []
    for linea, lang, cuerpo in bloques(text):
        if lang == "sql-vivo":
            out.append((linea, cuerpo.strip().rstrip(";")))
        elif lang == "reto":
            campos, actual = {}, None
            for line in cuerpo.splitlines():
                head, sep, rest = line.partition(":")
                if sep and head.strip() in ("pregunta", "inicio", "esperado", "pista", "solucion"):
                    actual = head.strip()
                    campos[actual] = [rest.strip()] if rest.strip() else []
                elif actual:
                    campos[actual].append(line.rstrip())
            for clave in ("inicio", "solucion"):
                sql = "\n".join(campos.get(clave, [])).strip().rstrip(";")
                if sql.lower().lstrip().startswith(("select", "with")):
                    out.append((linea, sql))
    return out


def main() -> None:
    if not BRONZE.exists():
        print("  no hay lago todavía: nada que comparar")
        return

    temario = json.loads(io.open(TEMARIO, encoding="utf-8").read())
    hechos = json.loads(io.open(SAMPLE_FACTS, encoding="utf-8").read())
    # La bandera la escribe make_sample.py. Antes se deducía comparando el
    # recuento de filas con el de la primera muestra, y eso trataba como
    # recortada cualquier muestra de otro grano, como las horarias del módulo 15.
    completas = {m["name"] for m in hechos["muestras"] if not m.get("recorta_filas")}
    un_dia = hechos["un_dia"]

    problemas, usadas, revisadas = [], set(), 0

    for module in temario["modules"]:
        tablas = declared(module)
        usadas.update(tablas.values())

        faltan = [f for f in tablas.values() if not (SAMPLES / f"{f}.parquet").exists()]
        if faltan:
            problemas.append(
                f"módulo {module['number']}: declara muestras que no existen: "
                f"{', '.join(faltan)}. Corre src/site/make_sample.py")
            continue

        lecciones = [LESSONS / f"{module['slug']}.md", LESSONS / "en" / f"{module['slug']}.md"]
        for path in [p for p in lecciones if p.exists()]:
            nombre = path.name + (" (en)" if path.parent.name == "en" else "")
            consultas = queries_of(path)
            if not consultas:
                continue
            muestra = connect_sample(tablas)
            lago = connect_lake(tablas)

            for linea, sql in consultas:
                revisadas += 1
                try:
                    en_muestra = muestra.sql(sql).fetchall()
                except Exception as e:
                    problemas.append(
                        f"{nombre}:{linea}  NO CORRE contra las muestras que baja el lector "
                        f"({', '.join(sorted(tablas.values()))}): "
                        f"{str(e).splitlines()[0][:90]}")
                    continue

                # Si ALGUNA de las muestras del módulo recorta filas, la consulta
                # tiene que decir de qué día habla. Si no, el lector ve una cosa y
                # el lago dice otra, y la lección publicaría la diferencia.
                #
                # Se miran todas y no solo `telemetria`: desde el módulo 15 hay
                # módulos que declaran sus vistas con otros nombres.
                recortadas = [f for f in tablas.values() if f not in completas]
                if recortadas:
                    if un_dia not in sql:
                        problemas.append(
                            f"{nombre}:{linea}  {', '.join(recortadas)} lleva un solo día "
                            f"y la consulta no filtra por {un_dia}")
                    continue

                try:
                    en_lago = lago.sql(sql).fetchall()
                except Exception as e:
                    problemas.append(f"{nombre}:{linea}  corre en la muestra y no en el lago: "
                                     f"{str(e).splitlines()[0][:70]}")
                    continue
                a = sorted([normaliza(v) for v in fila] for fila in en_muestra)
                b = sorted([normaliza(v) for v in fila] for fila in en_lago)
                if a != b:
                    problemas.append(
                        f"{nombre}:{linea}  da distinto en la muestra y en el lago: "
                        f"{len(a)} filas contra {len(b)}. El lector acertaría y la página "
                        f"le diría que no")
            muestra.close()
            lago.close()

    huerfanas = [p.stem for p in SAMPLES.glob("*.parquet") if p.stem not in usadas]
    for h in huerfanas:
        problemas.append(f"la muestra «{h}» no la usa ningún módulo: son bytes que nadie baja")

    print(f"  {len(usadas)} muestras declaradas, {revisadas} consultas ejecutadas contra ellas")
    for m in sorted(usadas):
        p = SAMPLES / f"{m}.parquet"
        quien = [str(x["number"]) for x in temario["modules"] if m in declared(x).values()]
        if p.exists():
            print(f"  {m:<24} {p.stat().st_size / 1024:>8.1f} KB   módulos {', '.join(quien)}")

    print()
    if problemas:
        for p in problemas:
            print(f"  {p}")
        raise SystemExit(f"{len(problemas)} problemas de muestra. No commitear.")
    print("Cada lección corre contra la muestra que su lector se baja, y dice lo mismo que el lago.")


if __name__ == "__main__":
    main()
