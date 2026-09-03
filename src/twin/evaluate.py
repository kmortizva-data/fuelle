"""The verdict: four failures, two counts, and the rival that was already there.

This is the module the whole course was walking towards, and it is also the one
with the most ways to cheat. Three of them are guarded against here.

**The first is grading your own exam.** The threshold gets swept, not chosen, and
every number is reported for the whole sweep. Module 27 measured the residual and
refused to pick a threshold precisely so this file could not measure and grade at
once.

**The second is calling a standing alarm a warning.** An alarm that fired twelve
days before a report gives twelve days of warning only if somebody would have
acted on it. If it had already been on for forty days, it gives nothing. So every
lead time here is reported next to **the length of the alarm episode it belongs
to**, and a lead that is a small slice of a long episode is not a warning.

**The third is comparing against nothing.** Two rivals: a plain threshold on the
duty cycle, and the low pressure alarm the machine already carries.

And one thing that has to be said out loud rather than buried. With constant
parameters,

    residual = carga x entrega - consumo

is an affine, increasing function of the duty cycle. So a threshold on the
residual and a threshold on the duty cycle **order the days identically**, and
this file checks that they do rather than asserting it. The twin does not win on
detection. What it wins is physical units, a calibration that needs no failure
history, and the ability to ask about a leak that has not happened yet.

Run:  .venv\\Scripts\\python.exe src\\twin\\evaluate.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from twin.model import MARZO, SANO, mide  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
PARTES = PROJECT / "src" / "ingest" / "failure_reports.csv"
RESIDUAL = PROJECT / "results" / "m27_residual.json"
RESULTS = PROJECT / "results" / "m28_veredicto.json"
PERILLAS = PROJECT / "assets" / "perillas"

LECTURAS_MINIMAS = 300
DIAS_DE_REFERENCIA = 14

# Los umbrales que se barren, del suelo de ruido para arriba. Por debajo del
# suelo no hay nada que discutir: la alarma sonaría en febrero.
UMBRALES = [round(0.10 + 0.05 * i, 3) for i in range(23)]      # 0,10 a 1,20


def carga_horas(con, entrega: float, consumo: float) -> None:
    """Las horas con su residual y su alarma instalada, sobre todo el registro."""
    con.execute(f"""
        CREATE OR REPLACE VIEW horas AS
        SELECT date_trunc('hour', timestamp) AS hora, day,
               avg(DV_eletric) AS carga,
               max(LPS) AS lps,
               avg(DV_eletric) * {entrega} - {consumo} AS residual
        FROM p GROUP BY 1, 2 HAVING count(*) >= {LECTURAS_MINIMAS}
    """)
    con.execute(f"""
        CREATE OR REPLACE VIEW dias AS
        WITH d AS (SELECT day, max(residual) AS pico, max(lps) AS lps
                   FROM horas GROUP BY day)
        SELECT *, pico - median(pico) OVER (
                    ORDER BY day
                    ROWS BETWEEN {DIAS_DE_REFERENCIA} PRECEDING AND 1 PRECEDING
                  ) AS sobre
        FROM d
    """)


def lee_partes(con) -> list[dict]:
    """Los cuatro partes, con los días que cubre cada uno."""
    salida = []
    for f in con.sql(f"""
        SELECT nr, strptime(start_time, '%-m/%-d/%Y %-H:%M'),
               strptime(end_time, '%-m/%-d/%Y %-H:%M')
        FROM read_csv_auto('{PARTES.as_posix()}') ORDER BY 2
    """).fetchall():
        ini, fin = f[1], f[2]
        dias = []
        d = ini.date()
        while d <= fin.date():
            dias.append(d)
            d += timedelta(days=1)
        salida.append({"nr": f[0], "empieza": ini, "acaba": fin, "dias": dias})
    return salida


def episodios(alarmas: list[date]) -> list[tuple[date, date]]:
    """Los días de alarma, agrupados en rachas seguidas.

    Hace falta porque **la antelación sola engaña**. Un aviso doce días antes de
    un parte vale doce días si la alarma se encendió entonces, y no vale nada si
    llevaba dos meses encendida.
    """
    if not alarmas:
        return []
    tramos, ini, prev = [], alarmas[0], alarmas[0]
    for d in alarmas[1:]:
        if (d - prev).days > 1:
            tramos.append((ini, prev))
            ini = d
        prev = d
    tramos.append((ini, prev))
    return tramos


def cuantos_meses(con) -> int:
    """Los meses que abarca el registro. El mismo divisor para todos los rivales.

    Estaba puesto a mano en un sitio y calculado en otro, así que el gemelo y la
    alarma instalada dividían sus falsas alarmas por meses distintos. Comparar
    dos tasas con denominadores distintos es la forma más silenciosa de ganar
    una comparación.
    """
    return int(con.sql(
        "SELECT count(DISTINCT date_trunc('month', day)) FROM dias").fetchone()[0])


def evalua(con, umbral: float, columna: str, partes: list[dict],
           marzo_cuenta: bool, meses: int) -> dict:
    """Qué hace un umbral: a quién pilla, cuándo avisa y a quién despierta."""
    alarmas = [f[0] for f in con.sql(
        f"SELECT day FROM dias WHERE {columna} > {umbral} ORDER BY day"
    ).fetchall()]
    conjunto = set(alarmas)
    rachas = episodios(alarmas)

    dias_de_marzo = set()
    d = date.fromisoformat(MARZO[0])
    while d <= date.fromisoformat(MARZO[1]):
        dias_de_marzo.add(d)
        d += timedelta(days=1)

    sucesos = [{"nr": p["nr"], "empieza": p["empieza"], "dias": set(p["dias"])}
               for p in partes]
    if marzo_cuenta:
        sucesos.append({"nr": "marzo", "empieza": datetime.fromisoformat(
            MARZO[0] + "T00:00:00"), "dias": dias_de_marzo})

    detectados, avisos = [], []
    for s in sucesos:
        pillado = bool(s["dias"] & conjunto)
        # La antelación: desde que se encendió la racha que llega al suceso.
        antes, largo = None, None
        for ini, fin in rachas:
            if ini < s["empieza"].date() <= fin + timedelta(days=1):
                antes = (s["empieza"].date() - ini).days
                largo = (fin - ini).days + 1
                break
        detectados.append({"suceso": s["nr"], "detectado": pillado,
                           "dias_de_antelacion": antes,
                           "dias_que_llevaba_la_alarma": largo})
        if antes is not None and antes > 0:
            avisos.append(antes)

    dias_de_suceso = set().union(*(s["dias"] for s in sucesos))
    falsas = sorted(conjunto - dias_de_suceso)
    return {
        "umbral": umbral,
        "dias_con_alarma": len(alarmas),
        "sucesos": len(sucesos),
        "detectados": sum(1 for d in detectados if d["detectado"]),
        "con_aviso_previo": len(avisos),
        "antelacion_mediana": (sorted(avisos)[len(avisos) // 2] if avisos else None),
        "falsas_alarmas": len(falsas),
        "falsas_por_mes": round(len(falsas) / meses, 1),
        "rachas": len(rachas),
        "detalle": detectados,
    }


def el_rival_del_ciclo(con, partes: list[dict]) -> dict:
    """El umbral sobre el ciclo de trabajo, que es el rival trivial.

    No se compara por resultados sino por **orden**: si los dos ordenan los días
    igual, cualquier umbral de uno tiene su gemelo exacto en el otro y no hay
    nada que ganar. Se comprueba, no se afirma.
    """
    filas = con.sql("""
        WITH d AS (SELECT day, max(residual) AS pico, max(carga) AS carga
                   FROM horas GROUP BY day)
        SELECT day, pico, carga FROM d ORDER BY day
    """).fetchall()
    por_residual = [f[0] for f in sorted(filas, key=lambda f: -f[1])]
    por_carga = [f[0] for f in sorted(filas, key=lambda f: -f[2])]
    return {"dias": len(filas),
            "mismo_orden": por_residual == por_carga,
            "primeros_por_residual": [str(d) for d in por_residual[:3]],
            "primeros_por_carga": [str(d) for d in por_carga[:3]]}


def el_rival_instalado(con, partes: list[dict], meses: int) -> dict:
    """La alarma de baja presión que la máquina ya lleva puesta.

    **Se cuenta sobre las lecturas crudas, no sobre las horas completas**, y esa
    decisión cambia el resultado por un factor de tres. Las horas del gemelo
    piden 300 lecturas de las 360 porque un ciclo de trabajo sacado de treinta
    lecturas no es el de esa hora. Pero la LPS no promedia nada: salta o no
    salta, y de hecho salta sobre todo en horas incompletas, con 167 lecturas de
    mediana, porque se dispara cuando el registro vuelve y la presión está baja.

    Aplicarle al rival un filtro pensado para el gemelo le quitaba 101 de sus 136
    horas. Habría salido mejor parado en falsas alarmas por una regla que no es
    suya, y eso es ganar una comparación por el reglamento.

    Lo que sí se mantiene igual para los dos es **el conjunto de días**: los que
    el gemelo puede juzgar, o sea los que tienen alguna hora completa.
    """
    alarmas = [f[0] for f in con.sql("""
        SELECT DISTINCT day FROM p
        WHERE LPS > 0 AND day IN (SELECT day FROM dias)
        ORDER BY day
    """).fetchall()]
    conjunto = set(alarmas)
    dias_de_parte = set().union(*(set(p["dias"]) for p in partes))
    detectados = sum(1 for p in partes if set(p["dias"]) & conjunto)
    # Cuántas de sus horas caen en horas incompletas, que es la razón de contarla
    # sobre lecturas crudas. Va publicado para que el criterio se pueda discutir.
    horas = con.sql("""
        WITH h AS (SELECT date_trunc('hour', timestamp) AS hora, count(*) AS n,
                          max(LPS) AS lps FROM p GROUP BY 1)
        SELECT count(*) FILTER (WHERE lps > 0),
               count(*) FILTER (WHERE lps > 0 AND n < 300) FROM h
    """).fetchone()
    return {"dias_con_alarma": len(alarmas), "de_cuatro_partes": detectados,
            "horas_con_alarma": int(horas[0]),
            "de_esas_en_horas_incompletas": int(horas[1]),
            "falsas_alarmas": len(conjunto - dias_de_parte),
            "falsas_por_mes": round(len(conjunto - dias_de_parte) / meses, 1),
            "meses_con_alarma": len({(d.year, d.month) for d in alarmas})}


def perilla_umbral(serie: list[dict], barrido: list[dict],
                   dias_de_suceso: set) -> dict:
    """Módulo 28: mover el umbral y ver acumularse el intercambio.

    El trazo que se mueve es **cuántos días lleva sonando la alarma** según
    avanza el registro, y el de referencia es cuántos días de avería ha habido.
    Los dos empiezan juntos en cero, y lo que se abre entre ellos con el umbral
    bajo es exactamente lo que cuesta bajarlo.
    """
    ideal, n = [], 0
    for x in serie:
        n += 1 if x["dia"] in dias_de_suceso else 0
        ideal.append(float(n))

    series = []
    for b in barrido:
        acumulado, n = [], 0
        for x in serie:
            valor = x["congelado"]
            n += 1 if valor is not None and valor > b["umbral"] else 0
            acumulado.append(float(n))
        series.append({
            "valor": b["umbral"],
            "trazo": acumulado,
            "carga": 0.0, "arranques": 0,
            "detecta": b["detectados"],
            "falsas": b["falsas_alarmas"],
        })
    # Arranca donde el barrido dice, que es el umbral más alto que aún los pilla
    # todos. El lector empieza en la respuesta y baja desde ahí, no al revés.
    todos = [b for b in barrido if b["detectados"] == b["sucesos"]]
    elegido = max(todos, key=lambda b: b["umbral"])["umbral"]
    return {
        "titulo": "el umbral, y lo que cuesta bajarlo",
        "etiqueta": "umbral",
        "unidad": "bar/min",
        "eje": "días con la alarma puesta, acumulados",
        "horas": 0,
        "nota": {
            "es": "con este umbral pilla {detecta} averías de cuatro, y despierta "
                  "a alguien {falsas} días sin motivo",
            "en": "at this threshold it catches {detecta} failures out of four, "
                  "and wakes someone on {falsas} days for nothing",
        },
        "referencia": {
            "valor": elegido, "trazo": ideal,
            "carga": 0.0, "arranques": 0, "detecta": 4, "falsas": 0,
        },
        "posiciones": series,
    }


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")
    if not RESIDUAL.exists():
        raise SystemExit("Faltan las cifras del 27. Corre src/twin/residual.py.")

    dep, _ = mide()
    suelo = json.load(io.open(RESIDUAL, encoding="utf-8"))["suelo"]["maximo"]
    con = duckdb.connect()
    con.execute(f"CREATE VIEW p AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet') WHERE medido")
    carga_horas(con, dep.entrega, dep.consumo)
    partes = lee_partes(con)
    meses = cuantos_meses(con)

    print(f"  el suelo de ruido del módulo 27 está en {suelo}, y de ahí para "
          "arriba se barre el umbral")
    print(f"  el registro abarca {meses} meses, y ese es el divisor de todos")
    print(f"  los cuatro partes cubren "
          f"{len(set().union(*(set(p['dias']) for p in partes)))} días")
    print()

    barridos = {}
    for etiqueta, columna in (("congelado", "pico"), ("móvil", "sobre")):
        for marzo in (True, False):
            clave = f"{etiqueta}, marzo {'cuenta' if marzo else 'no cuenta'}"
            barridos[clave] = [evalua(con, u, columna, partes, marzo, meses)
                               for u in UMBRALES]

    for clave, barrido in barridos.items():
        print(f"  {clave}")
        print("    umbral | detecta | avisa antes | antelación | falsas/mes")
        for b in barrido[::4]:
            ant = "-" if b["antelacion_mediana"] is None else f"{b['antelacion_mediana']} d"
            print(f"     {b['umbral']:>5} | {b['detectados']:>2} de {b['sucesos']} "
                  f"| {b['con_aviso_previo']:>11} | {ant:>10} | "
                  f"{b['falsas_por_mes']:>10}")
        print()

    rival_ciclo = el_rival_del_ciclo(con, partes)
    rival_lps = el_rival_instalado(con, partes, meses)
    print("  el rival trivial, un umbral sobre el ciclo de trabajo:")
    print(f"    ordena los {rival_ciclo['dias']} días igual que el residual: "
          f"{'SÍ' if rival_ciclo['mismo_orden'] else 'no'}")
    print("  el rival instalado, la alarma de baja presión de la máquina:")
    print(f"    salta {rival_lps['dias_con_alarma']} días, pilla "
          f"{rival_lps['de_cuatro_partes']} de los 4 partes, "
          f"{rival_lps['falsas_por_mes']} falsas al mes")

    payload = {
        "ventana_sana": list(SANO), "evento_de_marzo": list(MARZO),
        "suelo_del_27": suelo, "umbrales": UMBRALES, "meses": meses,
        "partes": [{"nr": p["nr"], "empieza": p["empieza"].isoformat(),
                    "dias": [str(d) for d in p["dias"]]} for p in partes],
        "dias_de_parte": len(set().union(*(set(p["dias"]) for p in partes))),
        "barridos": {k: [{kk: vv for kk, vv in b.items() if kk != "detalle"}
                         for b in v] for k, v in barridos.items()},
        "detalle": {k: [b["detalle"] for b in v] for k, v in barridos.items()},
        # La serie diaria, para que las figuras no la vuelvan a calcular con su
        # propia versión de la regla. Una sola definición y dos consumidores.
        "serie_diaria": [
            {"dia": str(f[0]), "congelado": round(float(f[1]), 4),
             "movil": None if f[2] is None else round(float(f[2]), 4),
             "lps": float(f[3])}
            for f in con.sql("SELECT day, pico, sobre, lps FROM dias ORDER BY day")
                        .fetchall()],
        "rival_del_ciclo": rival_ciclo,
        "rival_instalado": rival_lps,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)

    PERILLAS.mkdir(parents=True, exist_ok=True)
    dias_de_suceso = {d for p in partes for d in map(str, p["dias"])}
    perilla = perilla_umbral(payload["serie_diaria"],
                             barridos["congelado, marzo no cuenta"], dias_de_suceso)
    destino = PERILLAS / "m28_umbral.json"
    with io.open(destino, "w", encoding="utf-8") as fh:
        json.dump(perilla, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"  {destino.name:<20} {len(perilla['posiciones'])} posiciones, "
          f"{destino.stat().st_size / 1024:>6.1f} KB")
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que el módulo publica y que si deja de ser cierto hay que remirar.
    #
    #   1. El residual y el ciclo de trabajo ordenan igual. Es la frase más
    #      incómoda de la lección y tiene que estar comprobada, no supuesta.
    if not rival_ciclo["mismo_orden"]:
        raise SystemExit(
            "El residual y el ciclo de trabajo ya no ordenan los días igual. La "
            "lección publica que sí, y de ahí sale todo su argumento honesto.")


if __name__ == "__main__":
    main()
