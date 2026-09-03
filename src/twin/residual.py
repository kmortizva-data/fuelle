"""The residual, and the two roads to it. Module 27.

A twin's only product is its disagreement with the machine. Here that
disagreement has a closed form, because the receiver has to balance: over any
stretch, the air the compressor put in equals the air the plant took out. So

    aire movido por minuto = carga x entrega
    residual               = carga x entrega - consumo sano

in bar/min, which is what the plant is drawing **above what it drew when it was
healthy**. Nothing else is needed: no fitting, no history, no threshold yet.

Three things this file measures, and each one is a section of the lesson.

**1. The residual has to be hourly.** Failure #1b starts at 23:30, so at daily
grain it dirties half an hour of a day. Hourly it stands 7.5 times above the
healthy ceiling; daily it stands 1.09 times above it, which is not detection,
it is a coin toss. This is module 15 turned around: there the fast signal had to
come down to the slow grain, and here going down to the slow grain destroys it.

**2. The residual is censored from above.** When the compressor never stops,
duty is 1 and the residual pins at `llena`, whatever the leak really is. It says
"at least this much" and cannot say how much.

**3. There is a second road, and the two are complementary in an awkward way.**
The drain slope measures the plant's demand directly, with no model at all:
pressure drop divided by unloaded minutes. It is not censored, so it can report a
demand far above the ceiling. But it needs unloaded stretches to measure, and a
severe leak leaves none. So **the road that always answers cannot say how bad it
is, and the road that can say how bad it is sometimes does not answer**.

And one thing this file does NOT do, on purpose: decide a threshold. That is
module 28, and mixing the two would let the verdict choose its own evidence.

Run:  .venv\\Scripts\\python.exe src\\twin\\residual.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from twin.model import MARZO, SANO, _crea_tramos, mide  # noqa: E402
from twin.simulate import PUNTOS_DEL_TRAZO, avanza, recorta  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
PARTES = PROJECT / "src" / "ingest" / "failure_reports.csv"
RESULTS = PROJECT / "results" / "m27_residual.json"
PERILLAS = PROJECT / "assets" / "perillas"

# Una hora con menos de 300 lecturas de las 360 no se mide: le falta un sexto del
# reloj y su media de carga ya no es la de esa hora.
LECTURAS_MINIMAS = 300

# Cuántos días mira atrás la referencia móvil. Dos semanas es lo bastante corto
# para seguir una deriva de meses y lo bastante largo para no seguir una avería.
DIAS_DE_REFERENCIA = 14


def horas(con, entrega: float, consumo: float) -> None:
    """El residual hora a hora sobre todo el registro."""
    con.execute(f"""
        CREATE OR REPLACE VIEW horas AS
        SELECT date_trunc('hour', timestamp) AS hora,
               day,
               count(*) AS lecturas,
               avg(DV_eletric) AS carga,
               avg(LPS) AS lps,
               avg(DV_eletric) * {entrega} - {consumo} AS residual
        FROM p GROUP BY 1, 2 HAVING count(*) >= {LECTURAS_MINIMAS}
    """)


def suelo(con) -> dict:
    """Hasta dónde llega el residual cuando no pasa nada, que es el listón."""
    fila = con.sql(f"""
        SELECT count(*), median(residual), quantile_cont(residual, 0.95),
               quantile_cont(residual, 0.99), max(residual)
        FROM horas WHERE day BETWEEN DATE '{SANO[0]}' AND DATE '{SANO[1]}'
    """).fetchone()
    return {"horas_sanas": int(fila[0]), "mediana": round(float(fila[1]), 4),
            "p95": round(float(fila[2]), 4), "p99": round(float(fila[3]), 4),
            "maximo": round(float(fila[4]), 4)}


def grano(con, partes: list[dict]) -> list[dict]:
    """Por día contra por hora, en los cuatro partes. La #1b es la que decide."""
    salida = []
    for parte in partes:
        dia = parte["empieza"][:10]
        fila = con.sql(f"""
            SELECT (SELECT avg(DV_eletric) * {parte['entrega']} - {parte['consumo']}
                    FROM p WHERE day = DATE '{dia}'),
                   max(residual)
            FROM horas WHERE day = DATE '{dia}'
        """).fetchone()
        salida.append({"parte": parte["nr"], "dia": dia,
                       "diario": round(float(fila[0]), 4),
                       "horario_maximo": round(float(fila[1]), 4)})
    return salida


def censura(con, techo: float) -> dict:
    """Cuánto del registro está topado, que es cuánto el residual no puede decir."""
    fila = con.sql(f"""
        SELECT count(*), count(*) FILTER (WHERE carga >= 0.999),
               count(*) FILTER (WHERE residual >= {techo} - 0.01)
        FROM horas
    """).fetchone()
    return {"horas_medidas": int(fila[0]), "horas_al_cien": int(fila[1]),
            "horas_topadas": int(fila[2]), "techo": round(techo, 4)}


def movil(con) -> None:
    """El segundo indicador: cada día contra los catorce anteriores.

    Sobre el **máximo diario** y no sobre su mediana, y la diferencia no es de
    gusto. La #1b es de madrugada, así que con la mediana del día queda por
    debajo de la tendencia y el indicador la da por normal. Con el máximo, no.

    Esto no contradice la regla del módulo 23, que dice que el gemelo se calibra
    con lo sano y se congela. **El gemelo sigue congelado.** Lo que se mueve es
    la referencia contra la que se lee su residual, que es una segunda lectura
    del mismo número: el congelado dice cuánto se ha alejado la máquina de cuando
    estaba bien, y el móvil dice cuánto se ha alejado de la semana pasada.
    """
    con.execute(f"""
        CREATE OR REPLACE VIEW dias AS
        WITH d AS (
          SELECT day, max(residual) AS pico, median(residual) AS medio,
                 count(*) AS horas
          FROM horas GROUP BY day
        )
        SELECT *, median(pico) OVER (
                    ORDER BY day
                    ROWS BETWEEN {DIAS_DE_REFERENCIA} PRECEDING AND 1 PRECEDING
                  ) AS base,
               pico - median(pico) OVER (
                    ORDER BY day
                    ROWS BETWEEN {DIAS_DE_REFERENCIA} PRECEDING AND 1 PRECEDING
                  ) AS sobre_la_tendencia
        FROM d
    """)


def segunda_ruta(con) -> None:
    """El consumo medido por la pendiente de vaciado, sin modelo de por medio.

    Usa los mismos tramos que el módulo 24, con sus mismas reglas: minutos
    contados por intervalos y fuera los que saltan un hueco. Por eso `day` viaja
    ahora dentro de `tramos`, en vez de tener aquí una copia de la regla que se
    fuera separando de la original.
    """
    con.execute("""
        CREATE OR REPLACE VIEW pendiente AS
        SELECT day,
               count(*) AS tramos_de_vacio,
               sum(minutos) AS minutos_de_vacio,
               sum(p_ini - p_fin) / sum(minutos) AS consumo
        FROM tramos WHERE cargando = 0 AND roto = 0 AND lecturas > 1
        GROUP BY day
    """)


def perilla_fuga(dep, suelo_sano: float) -> dict:
    """Módulo 27: mover el caudal de fuga y ver a partir de qué tamaño se nota.

    Y hay una identidad que la hace exacta, no aproximada. Con una fuga de `f`
    bar/min, la máquina acaba cargando `(consumo + f) / entrega` del tiempo, así
    que

        residual = carga x entrega - consumo = f

    **el residual vale la fuga.** No se le parece: es ella, en las mismas
    unidades. Por eso la pregunta «a partir de qué tamaño se nota» tiene una
    respuesta de una línea: se nota cuando la fuga pasa del suelo de ruido, que
    en esta máquina son 0,1165 bar/min.
    """
    minutos = 8 * 60
    paso = 5 / 60          # el que salió del módulo 25
    fugas = [round(0.015 * i, 4) for i in range(21)]     # 0 a 0,30 bar/min
    base = avanza(dep, dep.consumo, minutos, paso)
    series = []
    for fuga in fugas:
        r = avanza(dep, dep.consumo + fuga, minutos, paso)
        residual = r["carga"] * dep.entrega - dep.consumo
        series.append({
            "valor": fuga,
            "trazo": recorta(r["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(r["carga"], 4),
            "arranques": r["arranques"],
            "residual": round(residual, 3),
            "veces_el_suelo": round(residual / suelo_sano, 1),
        })
    residual_base = base["carga"] * dep.entrega - dep.consumo
    return {
        "titulo": "la fuga, y a partir de qué tamaño el gemelo la nota",
        "etiqueta": "fuga",
        "unidad": "bar/min",
        "eje": "minutos cargando, acumulados",
        "horas": minutos / 60,
        "nota": {
            # Con «veces» delante de un número que se mueve, la posición que da
            # 1 escribiría «1 veces». El aspa no tiene ese problema.
            "es": "el residual queda en {residual} bar/min, {veces_el_suelo}× "
                  "el suelo de ruido",
            "en": "the residual comes out at {residual} bar/min, "
                  "{veces_el_suelo}× the noise floor",
        },
        "referencia": {
            "valor": 0.0,
            "trazo": recorta(base["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(base["carga"], 4),
            "arranques": base["arranques"],
            "residual": round(residual_base, 3),
            "veces_el_suelo": round(residual_base / suelo_sano, 1),
        },
        "posiciones": series,
    }


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    dep, contexto = mide()
    con = duckdb.connect()
    con.execute(f"CREATE VIEW p AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet') WHERE medido")
    horas(con, dep.entrega, dep.consumo)
    movil(con)
    _crea_tramos(con, "2020-01-01", "2020-12-31")
    segunda_ruta(con)

    partes = [{"nr": f[0], "empieza": str(f[1]), "acaba": str(f[2]),
               "entrega": dep.entrega, "consumo": dep.consumo}
              for f in con.sql(f"""
                  SELECT nr, strptime(start_time, '%-m/%-d/%Y %-H:%M'),
                         strptime(end_time, '%-m/%-d/%Y %-H:%M')
                  FROM read_csv_auto('{PARTES.as_posix()}') ORDER BY 2
              """).fetchall()]

    el_suelo = suelo(con)
    la_censura = censura(con, dep.llena)
    el_grano = grano(con, partes)

    print(f"  el residual es carga x {dep.entrega} - {dep.consumo}, en bar/min")
    print()
    print(f"  el suelo, sobre {el_suelo['horas_sanas']} horas de febrero:")
    print(f"    mediana {el_suelo['mediana']}   p95 {el_suelo['p95']}   "
          f"p99 {el_suelo['p99']}   máximo {el_suelo['maximo']}")
    print(f"  el techo, que es `llena`: {la_censura['techo']}   "
          f"o sea {la_censura['techo'] / el_suelo['maximo']:.1f} veces el suelo")
    print(f"  y {la_censura['horas_topadas']} horas de {la_censura['horas_medidas']} "
          f"llegan a tocarlo")

    print()
    print("  por día contra por hora, en los cuatro partes:")
    for g in el_grano:
        # Lo que dice si el grano diario sirve o no es **cuántas veces el suelo**
        # queda la señal, no si la cruza. Cruzarlo por un 9 % no es detectar.
        g["veces_el_suelo_diario"] = round(g["diario"] / el_suelo["maximo"], 2)
        g["veces_el_suelo_horario"] = round(
            g["horario_maximo"] / el_suelo["maximo"], 2)
        print(f"    {g['parte']:<4} {g['dia']}   diario {g['diario']:>7} "
              f"({g['veces_el_suelo_diario']:>5}x el suelo)   horario "
              f"{g['horario_maximo']:>7} ({g['veces_el_suelo_horario']:>5}x)")

    print()
    print("  la segunda ruta, el consumo por pendiente de vaciado:")
    ruta = []
    for f in con.sql(f"""
        SELECT h.day, d.tramos_de_vacio, round(d.minutos_de_vacio, 0),
               round(d.consumo, 4), round(h.pico, 4)
        FROM (SELECT day, max(residual) AS pico FROM horas GROUP BY day) h
        LEFT JOIN pendiente d USING (day)
        WHERE h.day IN (DATE '2020-02-18', DATE '2020-03-06', DATE '2020-04-18',
                        DATE '2020-05-30', DATE '2020-06-05', DATE '2020-06-06',
                        DATE '2020-07-15')
        ORDER BY h.day
    """).fetchall():
        # LEFT JOIN a propósito: los días sin ningún tramo de vacío tienen que
        # salir con un hueco, porque **el hueco es el resultado**.
        dia = str(f[0])
        if f[1] is None:
            print(f"    {dia}   sin un solo tramo de vacío: la ruta no contesta")
            ruta.append({"dia": dia, "tramos": 0, "consumo": None,
                         "residual_maximo": round(float(f[4]), 4)})
        else:
            print(f"    {dia}   {int(f[1]):>4} tramos, {float(f[2]):>6.0f} min   "
                  f"consumo {float(f[3])}   (el residual iba por {float(f[4])})")
            ruta.append({"dia": dia, "tramos": int(f[1]),
                         "minutos": float(f[2]), "consumo": float(f[3]),
                         "residual_maximo": round(float(f[4]), 4)})

    print()
    print("  y el indicador móvil, contra los 14 días anteriores:")
    tendencia = []
    for f in con.sql("""
        SELECT day, round(pico, 4), round(base, 4), round(sobre_la_tendencia, 4)
        FROM dias
        WHERE day IN (DATE '2020-03-06', DATE '2020-04-18', DATE '2020-05-29',
                      DATE '2020-06-05', DATE '2020-07-15')
        ORDER BY day
    """).fetchall():
        print(f"    {f[0]}   pico {f[1]:>7}   base {f[2]:>7}   "
              f"sobre la tendencia {f[3]:>7}")
        tendencia.append({"dia": str(f[0]), "pico": float(f[1]),
                          "base": float(f[2]), "sobre_la_tendencia": float(f[3])})

    # La deriva, que es lo que obliga a tener dos indicadores en vez de uno.
    deriva = [{"mes": f[0], "dias": int(f[1]), "sobre_el_suelo": int(f[2]),
               "residual_mediano": round(float(f[3]), 4)}
              for f in con.sql(f"""
                  SELECT strftime(day, '%Y-%m'), count(DISTINCT day),
                         count(DISTINCT CASE WHEN residual > {el_suelo['maximo']}
                                             THEN day END),
                         median(residual)
                  FROM horas GROUP BY 1 ORDER BY 1
              """).fetchall()]
    print()
    print("  la deriva, mes a mes:")
    for d in deriva:
        print(f"    {d['mes']}   {d['sobre_el_suelo']:>3} de {d['dias']:>3} días por "
              f"encima del suelo   residual mediano {d['residual_mediano']}")

    payload = {
        "entrega": dep.entrega, "consumo": dep.consumo,
        "ventana_sana": list(SANO), "evento_de_marzo": list(MARZO),
        "suelo": el_suelo, "censura": la_censura,
        "cuantas_veces_el_suelo": round(dep.llena / el_suelo["maximo"], 1),
        "grano": el_grano, "segunda_ruta": ruta, "tendencia": tendencia,
        "deriva": deriva, "dias_de_referencia": DIAS_DE_REFERENCIA,
        "partes": [{"nr": p["nr"], "empieza": p["empieza"], "acaba": p["acaba"]}
                   for p in partes],
        # Las series que dibuja la figura, ya en el grano que se publica.
        "serie_horaria": [{"hora": str(f[0]), "residual": round(float(f[1]), 4)}
                          for f in con.sql(
                              "SELECT hora, residual FROM horas ORDER BY hora"
                          ).fetchall()],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    # La perilla se escribe aquí y no en simulate.py porque necesita el suelo de
    # ruido, y el suelo sale de este fichero. Que la perilla y la cifra salgan de
    # la misma corrida es lo que impide que se separen.
    PERILLAS.mkdir(parents=True, exist_ok=True)
    perilla = perilla_fuga(dep, el_suelo["maximo"])
    destino = PERILLAS / "m27_fuga.json"
    with io.open(destino, "w", encoding="utf-8") as fh:
        json.dump(perilla, fh, ensure_ascii=False, separators=(",", ":"))
    cruza = next(p for p in perilla["posiciones"] if p["veces_el_suelo"] >= 1)
    print()
    print(f"  la perilla cruza el suelo con una fuga de {cruza['valor']} bar/min, "
          f"que es cuando el residual llega a {cruza['residual']}")
    print(f"  {destino.name:<20} {len(perilla['posiciones'])} posiciones, "
          f"{destino.stat().st_size / 1024:>6.1f} KB")
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Tres cosas que la lección publica, y que si dejan de ser ciertas hay que
    # remirar antes que reescribir la prosa.
    #
    #   1. El techo tiene que quedar muy por encima del suelo, o no hay margen.
    if dep.llena < el_suelo["maximo"] * 5:
        raise SystemExit(f"El techo ({dep.llena}) ya no está cinco veces por encima "
                         f"del suelo sano ({el_suelo['maximo']}). Sin margen no hay "
                         "residual que sirva.")
    #   2. La #1b tiene que perderse por días y verse por horas. Es el argumento
    #      entero de por qué el residual es horario.
    nocturna = [g for g in el_grano if g["dia"] == "2020-05-29"]
    if nocturna:
        g = nocturna[0]
        if not (g["veces_el_suelo_diario"] < 1.5 <= 3 < g["veces_el_suelo_horario"]):
            raise SystemExit(
                f"La avería del 29 de mayo ya no se hunde al bajar de grano: "
                f"diario {g['veces_el_suelo_diario']}x el suelo y horario "
                f"{g['veces_el_suelo_horario']}x. El módulo 27 publica que por "
                "días queda pegada al ruido y por horas no.")
    #   3. Y la segunda ruta tiene que quedarse muda en la avería más grave, que
    #      es lo que la hace complementaria y no redundante.
    abril = [r for r in ruta if r["dia"] == "2020-04-18"]
    if abril and abril[0]["tramos"] > 0:
        raise SystemExit(
            f"El 18 de abril ya tiene {abril[0]['tramos']} tramos de vacío. El "
            "módulo 27 publica que la pendiente no puede medir ahí.")


if __name__ == "__main__":
    main()
