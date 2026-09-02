"""The schema as a contract the engine enforces. Module 20.

Module 16 wrote the promises as queries a script ran. This writes the same
promises into the table itself, so the engine refuses the write instead of a
script noticing afterwards. That is the whole difference: a contract that
reports, against one that blocks.

And it gets tested the same way, because a guard nobody has seen refuse anything
proves nothing. Six impossible writes get attempted on purpose, one per kind of
guard, and the script counts how many the database rejects and keeps the error
it returned:

  1. a repeated timestamp                 -> primary key
  2. a pressure of -900 bar               -> CHECK on the range
  3. `medido` left empty                  -> NOT NULL
  4. a digital signal holding 2           -> CHECK on the accepted values
  5. a reading dated 2020-02-29           -> foreign key, that day does not exist
  6. a day with 30 loaded hours           -> CHECK, a day has 24

The fifth is the one worth stopping at. 2020-02-29 and 2020-04-26 are the two
days module 13 found missing from the record, so the foreign key is not a
formality: it makes a reading impossible on a day the lake never saw.

Run:  .venv\\Scripts\\python.exe src\\db\\schema.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.servidor import conecta, servidor  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT / "results" / "m20_esquema.json"

# El día que un compresor no puede pasar cargando. No es una opinión: son las
# horas que tiene un día.
HORAS_DE_UN_DIA = 24

# Cada guarda lleva SU nombre, y no es cosmética.
#
# Dos razones. La primera es que sin nombre PostgreSQL se inventa uno,
# `lecturas_tp2_check`, y al recrear la tabla mientras la vieja todavía existe le
# va pegando sufijos: `..._check1`, `..._check2`. El nombre publicado en una
# lección caducaría solo.
#
# La segunda pesa más. **El nombre de la guarda es lo único que el mensaje de
# error enseña a quien esté mirando a las tres de la mañana**, así que
# «tp2_en_rango» le dice qué ha pasado y «lecturas_tp2_check1» no.
ESQUEMA = f"""
CREATE TABLE dias (
    dia              date     CONSTRAINT dias_pk PRIMARY KEY,
    lecturas         integer  NOT NULL
                     CONSTRAINT dias_lecturas_no_negativas CHECK (lecturas >= 0),
    horas_de_carga   numeric  NOT NULL
                     CONSTRAINT horas_de_un_dia
                     CHECK (horas_de_carga BETWEEN 0 AND {HORAS_DE_UN_DIA})
);

CREATE TABLE lecturas (
    timestamp        timestamp CONSTRAINT lecturas_pk PRIMARY KEY,
    day              date      NOT NULL
                     CONSTRAINT el_dia_esta_en_el_calendario REFERENCES dias (dia),
    lecturas         integer   NOT NULL
                     CONSTRAINT lecturas_no_negativas CHECK (lecturas >= 0),
    medido           boolean   NOT NULL,
    dudoso           boolean   NOT NULL,
    tp2              double precision CONSTRAINT tp2_en_rango CHECK (tp2 BETWEEN -2 AND 15),
    tp3              double precision CONSTRAINT tp3_en_rango CHECK (tp3 BETWEEN -2 AND 15),
    h1               double precision,
    dv_pressure      double precision,
    reservoirs       double precision,
    oil_temperature  double precision,
    motor_current    double precision,
    comp             double precision CONSTRAINT comp_es_binaria CHECK (comp IN (0, 1)),
    dv_eletric       double precision
                     CONSTRAINT dv_eletric_es_binaria CHECK (dv_eletric IN (0, 1)),
    towers           double precision,
    mpg              double precision,
    lps              double precision CONSTRAINT lps_es_binaria CHECK (lps IN (0, 1)),
    pressure_switch  double precision,
    oil_level        double precision,
    caudal_impulses  double precision,
    CONSTRAINT el_dia_es_el_de_la_marca CHECK (day = timestamp::date)
);
"""

# Las seis escrituras imposibles. Cada una apunta a una guarda distinta, y
# ninguna da error al escribirla: son SQL perfectamente válido.
IMPOSIBLES = {
    "la misma marca de tiempo dos veces": """
        INSERT INTO lecturas (timestamp, day, lecturas, medido, dudoso)
        SELECT timestamp, day, lecturas, medido, dudoso FROM lecturas LIMIT 1
    """,
    "una presion de -900 bar": """
        INSERT INTO lecturas (timestamp, day, lecturas, medido, dudoso, tp2)
        VALUES (TIMESTAMP '2020-06-05 00:00:05', DATE '2020-06-05', 1, true, false, -900)
    """,
    "una casilla sin decir si se midio": """
        INSERT INTO lecturas (timestamp, day, lecturas, medido, dudoso)
        VALUES (TIMESTAMP '2020-06-05 00:00:15', DATE '2020-06-05', 1, NULL, false)
    """,
    "una digital que vale 2": """
        INSERT INTO lecturas (timestamp, day, lecturas, medido, dudoso, comp)
        VALUES (TIMESTAMP '2020-06-05 00:00:25', DATE '2020-06-05', 1, true, false, 2)
    """,
    # Un día de FUERA del registro, y el primer intento enseñó por qué tiene que
    # serlo. Estaba puesto el 2020-02-29, que el módulo 13 dio por desaparecido,
    # y lo rechazó la clave primaria en vez de la foránea: ese día SÍ existe en
    # la plata, como filas vacías. Es el módulo 14 cobrando su rejilla.
    "una lectura de un dia que no existe": """
        INSERT INTO lecturas (timestamp, day, lecturas, medido, dudoso)
        VALUES (TIMESTAMP '2019-01-01 12:00:00', DATE '2019-01-01', 1, true, false)
    """,
    "un dia con 30 horas de carga": """
        INSERT INTO dias (dia, lecturas, horas_de_carga)
        VALUES (DATE '2021-01-01', 8640, 30)
    """,
}


def construye(pg) -> dict:
    """Crea el esquema y lo llena desde la tabla ingenua del módulo 19."""
    import psycopg

    # Los datos se copian a una tabla de paso ANTES de tirar nada, porque el
    # esquema nuevo se llena de ellos y no de un CSV: ya están dentro del
    # servidor y volver a cargarlos costaría veinte segundos y 190 MB.
    #
    # `CREATE TABLE ... AS SELECT` a propósito, y no un `RENAME`. Renombrar
    # parecía más barato y hace que la segunda corrida se estrelle: la tabla
    # renombrada se lleva consigo sus guardas, así que sus nombres siguen
    # ocupados y el esquema nuevo no puede usarlos. Una copia no arrastra
    # ninguna, y eso es justo lo que hace falta aquí.
    pg.execute("DROP TABLE IF EXISTS origen")
    pg.execute("CREATE TABLE origen AS SELECT * FROM lecturas")
    pg.execute("DROP TABLE IF EXISTS lecturas CASCADE")
    pg.execute("DROP TABLE IF EXISTS dias CASCADE")
    pg.commit()

    for sentencia in filter(str.strip, ESQUEMA.split(";")):
        pg.execute(sentencia)
    pg.commit()

    pg.execute("""
        INSERT INTO dias (dia, lecturas, horas_de_carga)
        SELECT day,
               count(*),
               round((sum(CASE WHEN dv_eletric = 1 THEN 1 ELSE 0 END)
                      * 10 / 3600.0)::numeric, 2)
        FROM origen
        GROUP BY day
    """)
    pg.execute("""
        INSERT INTO lecturas
        SELECT timestamp, day, lecturas, medido, dudoso, tp2, tp3, h1, dv_pressure,
               reservoirs, oil_temperature, motor_current, comp, dv_eletric, towers,
               mpg, lps, pressure_switch, oil_level, caudal_impulses
        FROM origen
    """)
    pg.commit()

    filas = pg.execute("SELECT count(*) FROM lecturas").fetchone()[0]
    dias = pg.execute("SELECT count(*) FROM dias").fetchone()[0]
    pg.execute("DROP TABLE origen")
    pg.commit()
    return {"filas": filas, "dias": dias, "psycopg": psycopg}


def guardas(pg) -> list[dict]:
    """Lee del catálogo qué guardas tiene puestas la base. No de una lista mía."""
    filas = pg.execute("""
        SELECT c.conrelid::regclass::text AS tabla,
               c.contype,
               c.conname,
               pg_get_constraintdef(c.oid) AS definicion
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public' AND t.relname IN ('lecturas', 'dias')
        ORDER BY tabla, c.contype, c.conname
    """).fetchall()
    tipos = {"p": "clave primaria", "f": "clave foránea", "c": "condición", "n": "no vacío"}
    return [{"tabla": t, "tipo": tipos.get(k, k), "nombre": n, "definicion": d}
            for t, k, n, d in filas]


def guardas_por_columna(pg) -> list[dict]:
    """Qué guarda protege qué columna, leído del catálogo y no de una lista mía.

    Es lo que dibuja la figura. Se lee así por la misma razón que el módulo 17
    lee el manifest de dbt: si la base sabe decir cómo está protegida, enseñarlo
    contado por ella y no por mí.
    """
    con_restriccion = pg.execute("""
        SELECT t.relname, a.attname, c.contype
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN unnest(c.conkey) AS k(attnum) ON true
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
        WHERE n.nspname = 'public' AND t.relname IN ('lecturas', 'dias')
    """).fetchall()
    obligatorias = pg.execute("""
        SELECT table_name, column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name IN ('lecturas', 'dias')
          AND is_nullable = 'NO'
    """).fetchall()

    tipos = {"p": "clave primaria", "f": "clave foránea", "c": "condición"}
    mapa: dict[tuple[str, str], set[str]] = {}
    for tabla, columna, tipo in con_restriccion:
        mapa.setdefault((tabla, columna), set()).add(tipos.get(tipo, tipo))
    for tabla, columna in obligatorias:
        mapa.setdefault((tabla, columna), set()).add("no vacío")

    orden = {"clave primaria": 0, "clave foránea": 1, "no vacío": 2, "condición": 3}
    return [{"tabla": t, "columna": c, "guardas": sorted(g, key=orden.get)}
            for (t, c), g in sorted(mapa.items())]


def columnas_obligatorias(pg) -> int:
    return pg.execute("""
        SELECT count(*) FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name IN ('lecturas', 'dias')
          AND is_nullable = 'NO'
    """).fetchone()[0]


def prueba_las_imposibles(pg, psycopg) -> list[dict]:
    """Intenta las seis, y se queda con lo que la base contesta.

    Cada intento va en su propia transacción: en PostgreSQL un error aborta la
    transacción entera, así que sin el `ROLLBACK` la segunda escritura fallaría
    por culpa de la primera y el recuento saldría bien por el motivo equivocado.
    """
    resultados = []
    for que, sql in IMPOSIBLES.items():
        try:
            pg.execute(sql)
            pg.commit()
            resultados.append({"que": que, "la_rechaza": False, "error": None,
                               "guarda": None})
        except psycopg.errors.Error as e:
            pg.rollback()
            diag = e.diag
            resultados.append({
                "que": que,
                "la_rechaza": True,
                "guarda": diag.constraint_name or diag.column_name or "NOT NULL",
                "error": str(e).splitlines()[0].strip(),
            })
    return resultados


def main() -> None:
    with servidor():
        pg = conecta()
        hay = pg.execute("SELECT to_regclass('lecturas') IS NOT NULL").fetchone()[0]
        sobrante = pg.execute(
            "SELECT to_regclass('origen') IS NOT NULL").fetchone()[0]
        if not hay and sobrante:
            # Una corrida anterior se quedó a medias: renombró y se estrelló
            # después. Recuperarlo cuesta una línea y ahorra volver a cargar
            # 1.841.760 filas, que son veinte segundos y un CSV de 190 MB.
            print("  recuperando la tabla de una corrida anterior a medias")
            pg.execute("ALTER TABLE origen RENAME TO lecturas")
            pg.commit()
            hay = True
        if not hay:
            raise SystemExit("Falta la tabla «lecturas». Corre src/db/load_silver.py")

        print("  creando el esquema con sus reglas y llenándolo")
        hecho = construye(pg)
        psycopg = hecho.pop("psycopg")
        print(f"    {hecho['filas']:,} lecturas en {hecho['dias']} días")

        puestas = guardas(pg)
        obligatorias = columnas_obligatorias(pg)
        print(f"    {len(puestas)} guardas en el catálogo, "
              f"{obligatorias} columnas que no admiten vacío")

        print()
        print("  y ahora, seis escrituras imposibles:")
        intentos = prueba_las_imposibles(pg, psycopg)
        for r in intentos:
            marca = "la rechaza" if r["la_rechaza"] else "LA DEJA PASAR"
            print(f"    {marca:<14} {r['que']}")
            if r["error"]:
                print(f"                   {r['error'][:96]}")

        rechazadas = sum(1 for r in intentos if r["la_rechaza"])
        payload = {
            "filas": hecho["filas"],
            "dias": hecho["dias"],
            "guardas": len(puestas),
            "columnas_obligatorias": obligatorias,
            "escrituras_imposibles": len(intentos),
            "rechazadas": rechazadas,
            "detalle": intentos,
            "catalogo": puestas,
            "por_columna": guardas_por_columna(pg),
        }
        RESULTS.parent.mkdir(exist_ok=True)
        with io.open(RESULTS, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

        print()
        print(f"  la base rechaza {rechazadas} de {len(intentos)}")
        print(f"  escrito en {RESULTS.relative_to(PROJECT)}")
        pg.close()

        if rechazadas != len(intentos):
            escapan = [r["que"] for r in intentos if not r["la_rechaza"]]
            raise SystemExit(f"La base deja pasar {len(escapan)}: {', '.join(escapan)}. "
                             "Una guarda que no se ha visto rechazar nada no protege.")


if __name__ == "__main__":
    main()
