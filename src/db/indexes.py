"""What an index buys and what it costs, both measured. Module 21.

The question is module 6's, asked again of a different engine: **give me one
day**. There it decided how to lay Parquet out on disk; here it decides whether
to build an index, and the answer comes from the same place, a median of seven
runs with `distinguishable()` allowed to say there is no difference.

Three things get measured, and the third is the one usually left out:

  1. The query without an index, with the plan PostgreSQL chose.
  2. The same query with it, with the plan it chose instead.
  3. **What the index costs**: the disk it takes, and how much it slows writing.

Publishing only the first two would be the false green of module 16 applied to a
benchmark. An index is a trade, and a lesson that shows one side of a trade is
selling something.

Run:  .venv\\Scripts\\python.exe src\\db\\indexes.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.servidor import conecta, servidor  # noqa: E402
from medir import distinguishable, measure, times_slower  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT / "results" / "m21_indices.json"

# El día del módulo 13, el de la avería #3. Se repite a propósito: es la misma
# pregunta que el módulo 6 le hacía al Parquet.
UN_DIA = "2020-06-05"
INDICE = "lecturas_por_dia"
CREA_EL_INDICE = f"CREATE INDEX IF NOT EXISTS {INDICE} ON lecturas (day)"

PREGUNTA = f"""
    SELECT count(*) AS lecturas,
           round(avg(oil_temperature)::numeric, 2) AS aceite
    FROM lecturas
    WHERE day = DATE '{UN_DIA}'
"""

# Las filas que se escriben para medir lo que cuesta mantener el índice. Se hace
# sobre una tabla aparte y no sobre `lecturas`, porque medir una escritura sobre
# la tabla buena la dejaría distinta después de cada corrida.
FILAS_DE_PRUEBA = 200_000

# Cuantas veces se repite la pareja de medidas de lectura. Cuatro, porque con
# dos ya se vio que el factor baila y una horquilla necesita mas de dos puntos.
REPETICIONES_DEL_FACTOR = 4


def plan(pg, sql: str) -> str:
    """La primera línea del plan, que es la que dice si hay índice o no."""
    filas = pg.execute(f"EXPLAIN {sql}").fetchall()
    return "\n".join(f[0] for f in filas)


def tipo_de_plan(texto: str) -> str:
    for linea in texto.splitlines():
        limpia = linea.strip().lstrip("-> ").split(" on ")[0].split("  ")[0]
        if "Scan" in limpia:
            return limpia.strip()
    return texto.splitlines()[0].strip()


def kb_del_indice(pg, nombre: str) -> float:
    return float(pg.execute(
        "SELECT pg_relation_size(%s) / 1024.0", (nombre,)).fetchone()[0])


def crea_indice(pg) -> None:
    """El índice, puesto una vez y sin medir nada: lo que orquesta el módulo 29.

    `ANALYZE` va detrás por lo mismo que en `main()`: sin estadísticas frescas el
    planificador puede seguir recorriendo la tabla entera por costumbre.
    """
    pg.execute(CREA_EL_INDICE)
    pg.execute("ANALYZE lecturas")
    pg.commit()


def main() -> None:
    with servidor():
        pg = conecta()
        if not pg.execute("SELECT to_regclass('lecturas') IS NOT NULL").fetchone()[0]:
            raise SystemExit("Falta la tabla «lecturas». Corre src/db/load_silver.py "
                             "y src/db/schema.py")

        def sin_indice() -> None:
            pg.execute(f"DROP INDEX IF EXISTS {INDICE}")
            pg.commit()

        def con_indice() -> None:
            pg.execute(CREA_EL_INDICE)
            pg.commit()

        def pregunta():
            return pg.execute(PREGUNTA).fetchall()

        # --- Leer, sin y con ---------------------------------------------
        sin_indice()
        respuesta = pregunta()
        plan_sin = plan(pg, PREGUNTA)
        lento = measure(pregunta)

        con_indice()
        # ANALYZE para que el planificador tenga estadísticas frescas: sin esto
        # puede seguir eligiendo el recorrido completo por costumbre y la medida
        # compararía dos veces lo mismo.
        pg.execute("ANALYZE lecturas")
        pg.commit()
        plan_con = plan(pg, PREGUNTA)
        rapido = measure(pregunta)

        if pregunta() != respuesta:
            raise SystemExit("Con índice devuelve otra cosa. No es la misma pregunta.")

        se_distinguen = distinguishable(lento, rapido)
        factor = times_slower(lento, rapido) if se_distinguen else None

        # La pareja entera se repite cuatro veces, y no por desconfianza
        # gratuita: las dos primeras corridas de esto dieron 54,9 y 115,2 veces.
        # Con la lectura por indice en cuatro milesimas de segundo, el factor es
        # en buena parte ruido del reloj, asi que se mide varias veces y **se
        # publica la horquilla**, no un numero. Es la regla del modulo 7: cuanto
        # mas rapida es una medida, menos fiable es su factor.
        #
        # Las cuatro salen de la MISMA corrida a proposito, para que la leccion
        # pueda citarlas todas y las cuatro esten en results/.
        factores = [factor] if factor else []
        for _ in range(REPETICIONES_DEL_FACTOR - 1):
            sin_indice()
            otro_lento = measure(pregunta)
            con_indice()
            pg.execute("ANALYZE lecturas")
            pg.commit()
            otro_rapido = measure(pregunta)
            if distinguishable(otro_lento, otro_rapido):
                factores.append(times_slower(otro_lento, otro_rapido))

        print(f"  la pregunta pide {respuesta[0][0]:,} lecturas de un día")
        print(f"    sin índice  {lento.median:.4f} s  ({lento.minimum:.4f} a "
              f"{lento.maximum:.4f})   {tipo_de_plan(plan_sin)}")
        print(f"    con índice  {rapido.median:.4f} s  ({rapido.minimum:.4f} a "
              f"{rapido.maximum:.4f})   {tipo_de_plan(plan_con)}")
        print(f"    el factor, medido {len(factores)} veces: "
              f"{', '.join(f'{f:.1f}' for f in factores)}")

        kb = kb_del_indice(pg, INDICE)
        print(f"    el índice ocupa {kb / 1024:.1f} MB")

        # --- Y lo que cuesta escribir ------------------------------------
        #
        #     Sobre una tabla de usar y tirar: medir una escritura contra
        #     `lecturas` la dejaría con filas de más al terminar.
        print()
        print("  lo que cuesta mantenerlo, escribiendo:")
        pg.execute("DROP TABLE IF EXISTS carga_de_prueba")
        pg.execute("CREATE TABLE carga_de_prueba (timestamp timestamp, day date, "
                   "lecturas integer, oil_temperature double precision)")
        pg.commit()

        def vacia_sin_indice() -> None:
            pg.execute("DROP INDEX IF EXISTS carga_por_dia")
            pg.execute("TRUNCATE carga_de_prueba")
            pg.commit()

        def vacia_con_indice() -> None:
            pg.execute("TRUNCATE carga_de_prueba")
            pg.execute("CREATE INDEX IF NOT EXISTS carga_por_dia "
                       "ON carga_de_prueba (day)")
            pg.commit()

        def escribe() -> None:
            pg.execute(f"""
                INSERT INTO carga_de_prueba
                SELECT timestamp, day, lecturas, oil_temperature
                FROM lecturas LIMIT {FILAS_DE_PRUEBA}
            """)
            pg.commit()

        escritura_sin = measure(escribe, setup=vacia_sin_indice)
        escritura_con = measure(escribe, setup=vacia_con_indice)
        escribir_se_distingue = distinguishable(escritura_sin, escritura_con)
        peaje = (times_slower(escritura_con, escritura_sin)
                 if escribir_se_distingue else None)
        print(f"    sin índice  {escritura_sin.median:.3f} s")
        print(f"    con índice  {escritura_con.median:.3f} s")
        print(f"    {f'{peaje:.2f} veces más lento' if peaje else 'no se distinguen'}")

        pg.execute("DROP TABLE IF EXISTS carga_de_prueba")
        pg.commit()

        payload = {
            "dia": UN_DIA,
            "lecturas_del_dia": respuesta[0][0],
            "filas_de_la_tabla": pg.execute(
                "SELECT count(*) FROM lecturas").fetchone()[0],
            "leer": {
                "sin_indice": {"mediana": round(lento.median, 4),
                               "minimo": round(lento.minimum, 4),
                               "maximo": round(lento.maximum, 4),
                               "plan": tipo_de_plan(plan_sin)},
                "con_indice": {"mediana": round(rapido.median, 4),
                               "minimo": round(rapido.minimum, 4),
                               "maximo": round(rapido.maximum, 4),
                               "plan": tipo_de_plan(plan_con)},
                "se_distinguen": se_distinguen,
                "veces_mas_rapido": round(factor, 1) if factor else None,
                # Todos los factores de esta corrida. La distancia entre ellos es
                # el resultado que se publica, y no cualquiera de ellos suelto.
                "factores_observados": [round(f, 1) for f in factores],
                "factor_minimo": round(min(factores), 1) if factores else None,
                "factor_maximo": round(max(factores), 1) if factores else None,
            },
            "escribir": {
                "filas": FILAS_DE_PRUEBA,
                "sin_indice": {"mediana": round(escritura_sin.median, 3),
                               "minimo": round(escritura_sin.minimum, 3),
                               "maximo": round(escritura_sin.maximum, 3)},
                "con_indice": {"mediana": round(escritura_con.median, 3),
                               "minimo": round(escritura_con.minimum, 3),
                               "maximo": round(escritura_con.maximum, 3)},
                "se_distinguen": escribir_se_distingue,
                "veces_mas_lento": round(peaje, 2) if peaje else None,
            },
            "mb_del_indice": round(kb / 1024, 1),
            "plan_sin_indice": plan_sin,
            "plan_con_indice": plan_con,
        }
        RESULTS.parent.mkdir(exist_ok=True)
        with io.open(RESULTS, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print()
        print(f"  escrito en {RESULTS.relative_to(PROJECT)}")
        pg.close()


if __name__ == "__main__":
    main()
