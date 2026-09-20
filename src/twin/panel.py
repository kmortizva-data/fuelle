"""The panel: the whole semester, one day at a time. Module 30.

Somebody who is not going to read thirty one modules gets one page: a knob that
picks the day, the compressor's working minutes piling up against the twin's,
and one sentence saying what that day was. This file writes everything that page
shows, in both languages, and the browser only adds up minutes and swaps text.

That is the rule the knobs already follow, stretched to the verdict. The physics
runs once, here, and so does the decision about whether a day raised the alarm:
if the page wrote its own sentence, there would be two places that could
disagree about the same day.

Three things this file measures, because the lesson publishes them:

1. **What the semester weighs** in the reader's browser, for three ways of
   writing the same curves at six resolutions, compressed the way GitHub Pages
   compresses. How the numbers are written weighs more than how many there are.
2. **The day that tells the story alone**: 5 June, where the residual crosses
   the threshold at 10:00, the hour the failure report starts.
3. **That the panel and the verdict cannot disagree.** Counted day by day here,
   the alarms, the hits and the false alarms at the verdict's threshold have to
   add up to what module 28 published, or nothing gets written.

Run:  .venv\\Scripts\\python.exe src\\twin\\panel.py
"""

from __future__ import annotations

import gzip
import io
import itertools
import json
import sys
from datetime import date, datetime
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from formato import numero  # noqa: E402
from twin.evaluate import carga_horas, lee_partes  # noqa: E402
from twin.model import MARZO, mide  # noqa: E402
from twin.simulate import avanza  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESIDUAL = PROJECT / "results" / "m27_residual.json"
VEREDICTO = PROJECT / "results" / "m28_veredicto.json"
SIMULAR = PROJECT / "results" / "m25_simular.json"
RESULTS = PROJECT / "results" / "m30_panel.json"
PANEL = PROJECT / "assets" / "panel"

# Un punto cada diez minutos, 144 por día. El veredicto es horario, así que la
# curva no necesita más para decirlo; y los partes empiezan y acaban en horas y
# medias, que caen todas en un múltiplo de diez.
MINUTOS_POR_PUNTO = 10
PUNTOS = 24 * 60 // MINUTOS_POR_PUNTO

# Las resoluciones que se pesan para la lección, en minutos por punto.
RESOLUCIONES = [60, 30, 15, 10, 5, 1]

# GitHub Pages comprime a nivel 5. Se midió en el paso 8.1 contra lo que manda
# de verdad, byte a byte, así que se pesa como pesa en la red y no a ojo.
NIVEL_DE_PAGES = 5

# El día con el que abre el panel. A las 10:00 el residual salta al techo, que es
# la hora exacta a la que empieza el parte #3: las dos curvas se separan a la hora
# del parte, y no hay que leer nada más para verlo.
DIA_INICIAL = "2020-06-05"

# Los días que cuentan la historia: uno sano, uno de marzo, y los cuatro partes.
# Del segundo parte va el 30 de mayo y no el 29: el 29 la fuga se abre a las 23:30
# y la curva apenas se mueve, y el 30 se ve entera, hasta que el parte se cierra.
DIAS_QUE_CUENTAN = ["2020-02-18", "2020-03-12", "2020-04-18",
                    "2020-05-30", "2020-06-05", "2020-07-15"]

# Una marca del gráfico no se escribe en la misma fila que otra a menos de ocho
# horas, o las dos etiquetas se pisan en un móvil: a 375 px, ocho horas son unos
# 95 px de gráfico y una etiqueta como «parte #3 10:00» ocupa unos 85.
SEPARACION_DE_MARCAS = 8 * 60 // MINUTOS_POR_PUNTO

MESES = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}
MESES_CORTOS = {
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct",
           "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
           "Nov", "Dec"],
}

# La etiqueta de cada clase de día, que la página enseña junto a la frase.
ETIQUETAS = {
    "es": {"acierto": "acierto", "escapa": "se escapa", "falsa": "falsa alarma",
           "marzo_alarma": "marzo, con alarma", "marzo": "marzo, sin alarma",
           "encima": "sobre el ruido", "normal": "normal", "sin_juzgar": "sin juzgar"},
    "en": {"acierto": "hit", "escapa": "missed", "falsa": "false alarm",
           "marzo_alarma": "March, alarm", "marzo": "March, quiet",
           "encima": "above the noise", "normal": "normal", "sin_juzgar": "not judged"},
}

ATAJOS = {
    "es": {"2020-02-18": "18 feb, sano", "2020-03-12": "12 mar, sin parte",
           "2020-04-18": "18 abr, parte #1", "2020-05-30": "30 may, parte #1",
           "2020-06-05": "5 jun, parte #3", "2020-07-15": "15 jul, parte #4"},
    "en": {"2020-02-18": "18 Feb, healthy", "2020-03-12": "12 Mar, no report",
           "2020-04-18": "18 Apr, report #1", "2020-05-30": "30 May, report #1",
           "2020-06-05": "5 Jun, report #3", "2020-07-15": "15 Jul, report #4"},
}

MARCAS = {
    "es": {"alarma": "alarma {h}", "parte": "parte {n} {h}", "cierre": "cierra {h}"},
    "en": {"alarma": "alarm {h}", "parte": "report {n} {h}", "cierre": "closes {h}"},
}

# Las frases. Cada una se ha escrito con las reglas del manual delante: una idea
# por frase, tres comas como mucho y sin rayas. `check_prose` y `check_clarity`
# las vuelven a leer desde los ficheros que salen de aquí.
FRASES = {
    "es": {
        "abre": "El {fecha} el compresor cargó {m} h de las {r} h registradas. "
                "Con la máquina sana, el gemelo dice {g} h.",
        "normal": "El residual no pasa de {pico} bar/min, dentro del suelo de ruido: "
                  "es un día normal.",
        "encima": "El residual llega a {pico} bar/min a las {hp}, por encima del ruido "
                  "y por debajo del umbral de {umbral}: la alarma no salta.",
        "a_la_vez": "A las {h} el residual pasa del umbral y salta la alarma, a la misma "
                    "hora que empieza el parte {n}: acierto.",
        "parte_antes": "El parte {n} empieza a las {hp} y la alarma salta a las {h}: "
                       "acierto.",
        "alarma_antes": "La alarma salta a las {h}, antes de que empiece el parte {n} a "
                        "las {hp}: acierto.",
        "abierto": "La alarma salta a las {h}, con el parte {n} abierto desde el "
                   "{fecha_parte}: acierto.",
        "cierra": "El parte se cierra a las {hc}.",
        "escapa_hoy": "El parte {n} empieza a las {hp} y el residual solo llega a {pico} "
                      "bar/min: ese día la alarma no salta.",
        "escapa_sigue": "Sigue abierto el parte {n} y el residual solo llega a {pico} "
                        "bar/min: ese día la alarma no salta.",
        "detectado": "Salta el {fecha_alarma}, así que el parte queda detectado.",
        "perdido": "No salta en ninguno de sus días, así que el parte se queda sin "
                   "detectar.",
        "falsa": "La alarma salta a las {h} y no hay parte de avería: cuenta como falsa "
                 "alarma.",
        "a_tope": "En su hora más cargada el compresor pasó el {c} % del tiempo en carga: "
                  "puede ser una avería que nadie apuntó.",
        "marzo_alarma": "La alarma salta a las {h}. Es uno de los doce días de marzo con "
                        "la máquina averiada y sin parte: falsa alarma en la cuenta "
                        "principal, acierto si marzo cuenta como avería.",
        "marzo": "Es uno de los doce días de marzo con la máquina averiada y sin parte. "
                 "El residual llega a {pico} bar/min, por debajo del umbral: la alarma "
                 "no salta.",
        "sin_juzgar": "El {fecha} el registro solo tiene {r} h y ninguna hora completa, "
                      "así que el gemelo no juzga ese día.",
        "vacio": "El {fecha} no hay ni una lectura en el registro, así que el gemelo no "
                 "tiene nada que juzgar.",
    },
    "en": {
        "abre": "On {fecha} the compressor was loaded for {m} h of the {r} h on record. "
                "With the machine healthy, the twin says {g} h.",
        "normal": "The residual never goes above {pico} bar/min, inside the noise floor: "
                  "an ordinary day.",
        "encima": "The residual reaches {pico} bar/min at {hp}, above the noise and below "
                  "the {umbral} threshold: the alarm stays quiet.",
        "a_la_vez": "At {h} the residual crosses the threshold and the alarm fires, the "
                    "same hour report {n} begins: a hit.",
        "parte_antes": "Report {n} begins at {hp} and the alarm fires at {h}: a hit.",
        "alarma_antes": "The alarm fires at {h}, before report {n} begins at {hp}: a hit.",
        "abierto": "The alarm fires at {h}, with report {n} open since {fecha_parte}: "
                   "a hit.",
        "cierra": "The report closes at {hc}.",
        "escapa_hoy": "Report {n} begins at {hp} and the residual only reaches {pico} "
                      "bar/min: the alarm stays quiet that day.",
        "escapa_sigue": "Report {n} is still open and the residual only reaches {pico} "
                        "bar/min: the alarm stays quiet that day.",
        "detectado": "It fires on {fecha_alarma}, so the report is still caught.",
        "perdido": "It fires on none of its days, so the report goes undetected.",
        "falsa": "The alarm fires at {h} and there is no failure report: it counts as a "
                 "false alarm.",
        "a_tope": "In its busiest hour the compressor was loaded {c} % of the time: it "
                  "may be a failure nobody wrote down.",
        "marzo_alarma": "The alarm fires at {h}. This is one of the twelve March days "
                        "with the machine failing and no report: a false alarm in the "
                        "main count, a hit if March counts as a failure.",
        "marzo": "This is one of the twelve March days with the machine failing and no "
                 "report. The residual reaches {pico} bar/min, below the threshold: the "
                 "alarm stays quiet.",
        "sin_juzgar": "On {fecha} the record holds only {r} h and not one complete hour, "
                      "so the twin does not judge that day.",
        "vacio": "On {fecha} there is not a single reading in the record, so the twin has "
                 "nothing to judge.",
    },
}

BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


# --------------------------------------------------------------- los números

def horas(minutos: float, lang: str) -> str:
    """Horas con dos decimales, salvo que sean redondas: «24 h», no «24,00 h»."""
    h = minutos / 60
    return numero(h, 0 if abs(h - round(h)) < 0.005 else 2, lang)


def fecha(d: date, lang: str) -> str:
    mes = MESES[lang][d.month - 1]
    return f"{d.day} de {mes}" if lang == "es" else f"{d.day} {mes}"


def fecha_corta(d: date, lang: str) -> str:
    return f"{d.day} {MESES_CORTOS[lang][d.month - 1]} {d.year}"


def reloj(momento: datetime) -> str:
    return momento.strftime("%H:%M")


# ------------------------------------------------------------- los tramos

def lee_minutos(con) -> dict[str, dict[str, list[float]]]:
    """Minutos cargando y minutos registrados de cada minuto del día, día a día.

    Se lee al minuto una sola vez y de ahí se agrupa a cualquier resolución, así
    que las seis que se pesan salen de los mismos datos y no de seis consultas.
    """
    dias: dict[str, dict[str, list[float]]] = {}
    for dia, minuto, cargado, registrado in con.sql("""
        SELECT day, hour(timestamp) * 60 + minute(timestamp),
               sum(CASE WHEN medido THEN coalesce(DV_eletric, 0) ELSE 0 END) / 6.0,
               count(*) FILTER (WHERE medido) / 6.0
        FROM s GROUP BY 1, 2
    """).fetchall():
        d = dias.setdefault(str(dia), {"cargado": [0.0] * 1440,
                                       "registrado": [0.0] * 1440})
        d["cargado"][minuto] = float(cargado)
        d["registrado"][minuto] = float(registrado)
    return dict(sorted(dias.items()))


def agrupa(serie: list[float], minutos: int) -> list[float]:
    return [sum(serie[i:i + minutos]) for i in range(0, len(serie), minutos)]


def acumula(tramos: list[float]) -> list[float]:
    return list(itertools.accumulate(tramos))


def en_tramos(acumulado: list[float]) -> list[int]:
    """Los minutos de cada tramo, enteros, sin arrastrar el redondeo.

    Redondear cada tramo por separado deja que el error se sume tramo a tramo, y
    con el gemelo, que carga poco y a menudo, se nota: `redondeo_por_tramo` lo
    mide abajo. Redondear el acumulado y restar no arrastra nada, porque la suma
    de los tramos vuelve a dar el acumulado redondeado, exacto, en cada punto.
    """
    redondo = [round(v) for v in acumulado]
    return [b - a for a, b in zip([0] + redondo, redondo)]


def gemelo_del_dia(dep, registrado_min: list[float], paso: float) -> list[float]:
    """Lo que habría cargado la máquina sana, sobre el mismo reloj registrado.

    El gemelo solo corre mientras hay registro. Si corriera también en los
    huecos, la máquina se quedaría quieta en ellos y el gemelo no, y las dos
    curvas se separarían por una razón que no tiene nada que ver con el aire.

    Devuelve el trabajo acumulado al final de cada minuto del día, en minutos.
    """
    total = sum(registrado_min)
    if total <= 0:
        return [0.0] * len(registrado_min)
    trabajo = avanza(dep, dep.consumo, total, paso)["trabajo"]
    salida, visto = [], 0.0
    for m in registrado_min:
        visto += m
        i = min(int(round(visto / paso)) - 1, len(trabajo) - 1)
        salida.append(trabajo[i] if i >= 0 else 0.0)
    return salida


def huecos(registrado: list[float]) -> list[list[int]]:
    """Los tramos sin una sola lectura, juntados en intervalos [desde, hasta)."""
    salida: list[list[int]] = []
    for i, m in enumerate(registrado):
        if m > 0:
            continue
        if salida and salida[-1][1] == i:
            salida[-1][1] = i + 1
        else:
            salida.append([i, i + 1])
    return salida


# ------------------------------------------------------------- el peso

def pesa(objeto) -> dict:
    """Lo que ocupa en disco y lo que viaja por la red, comprimido como Pages."""
    crudo = json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"kb": round(len(crudo) / 1024, 1),
            "kb_red": round(len(gzip.compress(crudo, compresslevel=NIVEL_DE_PAGES,
                                              mtime=0)) / 1024, 1)}


def escrituras(curvas: dict[str, list[list[float]]]) -> dict:
    """Las mismas curvas escritas de tres maneras, y lo que pesa cada una.

    A: el acumulado en horas con dos decimales, que es lo primero que se le
       ocurre a cualquiera porque es lo que se dibuja.
    B: los minutos de cada tramo, enteros.
    C: esos mismos minutos, un carácter por tramo. Solo cabe mientras ningún
       tramo pase de 35 minutos, así que con tramos de una hora no existe.
    """
    a = {d: [[round(v / 60, 2) for v in s] for s in series]
         for d, series in curvas.items()}
    b = {d: [en_tramos(s) for s in series] for d, series in curvas.items()}
    mayor_tramo = max(max(s) for series in b.values() for s in series)
    c = ({d: ["".join(BASE36[t] for t in s) for s in series] for d, series in b.items()}
         if mayor_tramo < len(BASE36) else None)
    return {"acumulado": pesa(a), "tramos": pesa(b),
            "caracteres": pesa(c) if c else None}


# ------------------------------------------------------------- el veredicto

def clase(pico: float | None, umbral: float, suelo: float,
          partes_del_dia: list[dict], marzo: bool) -> str:
    """Qué fue ese día, con las reglas del módulo 28 y en su mismo orden."""
    if pico is None:
        return "sin_juzgar"
    if pico > umbral:
        if partes_del_dia:
            return "acierto"
        return "marzo_alarma" if marzo else "falsa"
    if partes_del_dia:
        return "escapa"
    if marzo:
        return "marzo"
    return "encima" if pico > suelo else "normal"


def marcas(dia: date, alarma: datetime | None, partes_del_dia: list[dict],
           lang: str) -> list[dict]:
    """Las rayas verticales del gráfico: cuándo salta la alarma y cuándo el parte.

    Cada una lleva su fila, calculada aquí para que dos etiquetas cercanas no se
    pisen. La página solo las coloca.
    """
    salida = []
    if alarma is not None:
        salida.append({"x": (alarma.hour * 60 + alarma.minute) / MINUTOS_POR_PUNTO,
                       "tipo": "alarma",
                       "t": MARCAS[lang]["alarma"].format(h=reloj(alarma))})
    for p in partes_del_dia:
        if p["empieza"].date() == dia:
            salida.append({"x": (p["empieza"].hour * 60 + p["empieza"].minute)
                                / MINUTOS_POR_PUNTO,
                           "tipo": "parte",
                           "t": MARCAS[lang]["parte"].format(n=p["nr"],
                                                             h=reloj(p["empieza"]))})
        # Un parte que acaba a las 23:59 acaba con el día: no hay nada que marcar.
        if p["acaba"].date() == dia and reloj(p["acaba"]) != "23:59":
            salida.append({"x": (p["acaba"].hour * 60 + p["acaba"].minute)
                                / MINUTOS_POR_PUNTO,
                           "tipo": "cierre",
                           "t": MARCAS[lang]["cierre"].format(h=reloj(p["acaba"]))})
    salida.sort(key=lambda m: (m["x"], m["tipo"] != "alarma"))
    filas: list[list[float]] = []
    for m in salida:
        for fila, ocupadas in enumerate(filas):
            if all(abs(m["x"] - x) >= SEPARACION_DE_MARCAS for x in ocupadas):
                ocupadas.append(m["x"])
                m["fila"] = fila
                break
        else:
            filas.append([m["x"]])
            m["fila"] = len(filas) - 1
    return salida


def frase(dia: date, lang: str, cls: str, datos: dict, partes_del_dia: list[dict],
          alarmas_por_parte: dict[str, list[date]], umbral: float) -> str:
    """El veredicto del día, en una o dos frases, ya escrito."""
    f = FRASES[lang]
    n = lambda v, d=2: numero(v, d, lang)  # noqa: E731
    if cls == "sin_juzgar":
        if datos["registrado"] <= 0:
            return f["vacio"].format(fecha=fecha(dia, lang))
        return f["sin_juzgar"].format(fecha=fecha(dia, lang),
                                      r=horas(datos["registrado"], lang))

    trozos = [f["abre"].format(fecha=fecha(dia, lang), m=horas(datos["cargado"], lang),
                               r=horas(datos["registrado"], lang),
                               g=horas(datos["gemelo"], lang))]
    pico = n(datos["pico"])
    h = reloj(datos["alarma"]) if datos["alarma"] else None
    hp = reloj(datos["hora_pico"])

    if cls == "normal":
        trozos.append(f["normal"].format(pico=pico))
    elif cls == "encima":
        trozos.append(f["encima"].format(pico=pico, hp=hp, umbral=n(umbral)))
    elif cls == "acierto":
        p = partes_del_dia[0]
        if p["empieza"].date() == dia:
            empieza = reloj(p["empieza"])
            if empieza[:2] == h[:2]:
                trozos.append(f["a_la_vez"].format(h=h, n=p["nr"]))
            elif p["empieza"] < datos["alarma"]:
                trozos.append(f["parte_antes"].format(n=p["nr"], hp=empieza, h=h))
            else:
                trozos.append(f["alarma_antes"].format(h=h, n=p["nr"], hp=empieza))
        else:
            desde = f"{fecha(p['empieza'].date(), lang)} " + (
                f"a las {reloj(p['empieza'])}" if lang == "es"
                else f"at {reloj(p['empieza'])}")
            trozos.append(f["abierto"].format(h=h, n=p["nr"], fecha_parte=desde))
        if p["acaba"].date() == dia and reloj(p["acaba"]) != "23:59":
            trozos.append(f["cierra"].format(hc=reloj(p["acaba"])))
    elif cls == "escapa":
        p = partes_del_dia[0]
        if p["empieza"].date() == dia:
            trozos.append(f["escapa_hoy"].format(n=p["nr"], hp=reloj(p["empieza"]),
                                                 pico=pico))
        else:
            trozos.append(f["escapa_sigue"].format(n=p["nr"], pico=pico))
        despues = [d for d in alarmas_por_parte[p["clave"]] if d != dia]
        if despues:
            trozos.append(f["detectado"].format(fecha_alarma=fecha(despues[0], lang)))
        else:
            trozos.append(f["perdido"])
    elif cls == "falsa":
        trozos.append(f["falsa"].format(h=h))
        if datos["carga_maxima"] >= 0.95:
            trozos.append(f["a_tope"].format(c=n(datos["carga_maxima"] * 100, 0)))
    elif cls == "marzo_alarma":
        trozos.append(f["marzo_alarma"].format(h=h))
    elif cls == "marzo":
        trozos.append(f["marzo"].format(pico=pico))
    return " ".join(trozos)


# ------------------------------------------------------------------ main

def main() -> None:
    for falta, quien in ((SILVER, "src/transform/silver.py"),
                         (RESIDUAL, "src/twin/residual.py"),
                         (VEREDICTO, "src/twin/evaluate.py"),
                         (SIMULAR, "src/twin/simulate.py")):
        if not falta.exists():
            raise SystemExit(f"Falta {falta.relative_to(PROJECT)}. Corre {quien} primero.")

    residual = json.load(io.open(RESIDUAL, encoding="utf-8"))
    veredicto = json.load(io.open(VEREDICTO, encoding="utf-8"))
    simular = json.load(io.open(SIMULAR, encoding="utf-8"))
    suelo = residual["suelo"]["maximo"]
    # El umbral no se escribe a mano: es el que eligió el barrido del módulo 28,
    # el más alto que todavía pilla los cuatro partes.
    principal = veredicto["barridos"]["congelado, marzo no cuenta"]
    umbral = max(b["umbral"] for b in principal if b["detectados"] == b["sucesos"])
    paso = simular["paso_mas_grande_que_vale"] / 60

    dep, _ = mide()
    con = duckdb.connect()
    # Un solo hilo, por la regla del módulo 29: lo que se escribe tiene que salir
    # igual cada vez, y una media sumada en otro orden cambia su último decimal.
    con.execute("SET threads = 1")
    con.execute(f"CREATE VIEW s AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet')")
    con.execute("CREATE VIEW p AS SELECT * FROM s WHERE medido")
    carga_horas(con, dep.entrega, dep.consumo)
    partes = lee_partes(con)
    for i, p in enumerate(partes):
        p["clave"] = f"{p['nr']}@{i}"   # dos partes se llaman #1, erratas de fábrica

    # La hora del pico es la primera de las que empatan: los días de avería pasan
    # horas enteras clavados en el techo, y `arg_max` elegiría una cualquiera.
    por_dia = {str(f[0]): {"pico": float(f[1]), "alarma": f[2], "hora_pico": f[3],
                           "carga_maxima": float(f[4])}
               for f in con.sql(f"""
                   WITH d AS (SELECT day, max(residual) AS pico, max(carga) AS cmax
                              FROM horas GROUP BY day)
                   SELECT d.day, d.pico,
                          (SELECT min(h.hora) FROM horas h
                           WHERE h.day = d.day AND h.residual > {umbral}),
                          (SELECT min(h.hora) FROM horas h
                           WHERE h.day = d.day AND h.residual = d.pico),
                          d.cmax
                   FROM d ORDER BY d.day
               """).fetchall()}

    minutos = lee_minutos(con)
    zona_por_minuto = (dep.consumo + suelo) / dep.entrega
    print(f"  {len(minutos)} días de calendario, {len(por_dia)} con alguna hora completa")
    print(f"  el umbral del veredicto: {umbral} bar/min, y el suelo de ruido: {suelo}")
    print(f"  la zona sana acumula {zona_por_minuto:.4f} minutos de carga por minuto "
          f"registrado")

    # --- Las tres curvas de cada día, al minuto. De aquí sale todo lo demás.
    al_minuto: dict[str, list[list[float]]] = {}
    for d, x in minutos.items():
        maquina = acumula(x["cargado"])
        registrado = acumula(x["registrado"])
        gemelo = gemelo_del_dia(dep, x["registrado"], paso)
        zona = [v * zona_por_minuto for v in registrado]
        al_minuto[d] = [maquina, gemelo, zona]

    # --- Lo que pesa, en seis resoluciones y tres escrituras.
    pesos = []
    for mpp in RESOLUCIONES:
        # El acumulado al final de cada tramo: el último minuto de cada grupo.
        curvas = {d: [s[mpp - 1::mpp] for s in series] for d, series in al_minuto.items()}
        pesos.append({"minutos_por_punto": mpp, "puntos_por_dia": 1440 // mpp,
                      **escrituras(curvas)})
    print()
    print("  lo que pesa el semestre entero, tres curvas por día, en KB por la red:")
    print("    puntos/día | acumulado | tramos | caracteres")
    for p in pesos:
        c = p["caracteres"]["kb_red"] if p["caracteres"] else "-"
        print(f"    {p['puntos_por_dia']:>10} | {p['acumulado']['kb_red']:>9} | "
              f"{p['tramos']['kb_red']:>6} | {c:>10}")

    # --- La trampa del redondeo, medida: tramo a tramo contra acumulado y restar.
    peor_por_tramo, peor_acumulado = 0.0, 0.0
    for d, series in al_minuto.items():
        for s in series:
            curva = s[MINUTOS_POR_PUNTO - 1::MINUTOS_POR_PUNTO]
            tramos = [b - a for a, b in zip([0.0] + curva, curva)]
            por_tramo = acumula([round(t) for t in tramos])
            bien = acumula(en_tramos(curva))
            peor_por_tramo = max(peor_por_tramo,
                                 max(abs(a - b) for a, b in zip(por_tramo, curva)))
            peor_acumulado = max(peor_acumulado,
                                 max(abs(a - b) for a, b in zip(bien, curva)))
    print()
    print(f"  el redondeo, en el peor punto de todo el semestre:")
    print(f"    tramo a tramo        {peor_por_tramo:>6.1f} min de error")
    print(f"    acumulado y restar   {peor_acumulado:>6.1f} min de error")

    # --- Los días, con su clase, sus marcas y su frase.
    alarmas = {d for d, v in por_dia.items() if v["alarma"] is not None}
    alarmas_por_parte = {p["clave"]: sorted(dd for dd in p["dias"] if str(dd) in alarmas)
                         for p in partes}
    inicio_marzo, fin_marzo = (date.fromisoformat(v) for v in MARZO)

    registros = []
    for d, x in minutos.items():
        dia = date.fromisoformat(d)
        partes_del_dia = [p for p in partes if dia in p["dias"]]
        v = por_dia.get(d)
        cargado, registrado = sum(x["cargado"]), sum(x["registrado"])
        gemelo = al_minuto[d][1][-1]
        cls = clase(v["pico"] if v else None, umbral, suelo, partes_del_dia,
                    inicio_marzo <= dia <= fin_marzo)
        curva = {nombre: s[MINUTOS_POR_PUNTO - 1::MINUTOS_POR_PUNTO]
                 for nombre, s in zip(("maquina", "gemelo", "zona"), al_minuto[d])}
        registros.append({
            "dia": d, "fecha": dia, "clase": cls, "partes": partes_del_dia,
            "datos": {"pico": v["pico"] if v else None,
                      "alarma": v["alarma"] if v else None,
                      "hora_pico": v["hora_pico"] if v else None,
                      "carga_maxima": v["carga_maxima"] if v else 0.0,
                      "cargado": cargado, "registrado": registrado, "gemelo": gemelo,
                      "zona": al_minuto[d][2][-1]},
            "curvas": {k: en_tramos(s) for k, s in curva.items()},
            "huecos": huecos(agrupa(x["registrado"], MINUTOS_POR_PUNTO)),
        })

    cuenta: dict[str, int] = {}
    for r in registros:
        cuenta[r["clase"]] = cuenta.get(r["clase"], 0) + 1
    print()
    print("  los días, por clase:")
    for k in ("acierto", "escapa", "falsa", "marzo_alarma", "marzo", "encima",
              "normal", "sin_juzgar"):
        print(f"    {ETIQUETAS['es'][k]:<18} {cuenta.get(k, 0):>4}")

    # --- Un fichero por idioma. Las curvas son las mismas; las frases no.
    PANEL.mkdir(parents=True, exist_ok=True)
    indices = {r["dia"]: i for i, r in enumerate(registros)}
    ficheros = {}
    for lang in ("es", "en"):
        dias = []
        for r in registros:
            datos = r["datos"]
            dias.append({
                "dia": r["dia"],
                "fecha": fecha_corta(r["fecha"], lang),
                "clase": r["clase"],
                "etiqueta": ETIQUETAS[lang][r["clase"]],
                "pico": None if datos["pico"] is None else round(datos["pico"], 4),
                **r["curvas"],
                "huecos": r["huecos"],
                "marcas": marcas(r["fecha"], datos["alarma"], r["partes"], lang),
                "frase": frase(r["fecha"], lang, r["clase"], datos, r["partes"],
                               alarmas_por_parte, umbral),
                "leyenda": {"maquina": horas(datos["cargado"], lang) + " h",
                            "gemelo": horas(datos["gemelo"], lang) + " h",
                            "zona": horas(datos["zona"], lang) + " h",
                            "sin_registro": horas(1440 - datos["registrado"], lang)
                                            + " h"},
            })
        payload = {
            "idioma": lang,
            "minutos_por_punto": MINUTOS_POR_PUNTO,
            "puntos": PUNTOS,
            "techo_min": 24 * 60,
            "umbral": umbral,
            "suelo": suelo,
            "techo_residual": dep.llena,
            "inicial": indices[DIA_INICIAL],
            "atajos": [{"i": indices[d], "t": ATAJOS[lang][d]} for d in DIAS_QUE_CUENTAN],
            "dias": dias,
        }
        destino = PANEL / f"semestre.{lang}.json"
        with io.open(destino, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
        ficheros[lang] = {"fichero": destino.name, **pesa(payload)}
        print(f"  {destino.name:<20} {ficheros[lang]['kb']:>7} KB en disco, "
              f"{ficheros[lang]['kb_red']:>6} KB por la red")

    # --- Lo que la lección cita, con sus números.
    def resumen(d: str) -> dict:
        r = registros[indices[d]]
        datos = r["datos"]
        return {"dia": d, "clase": r["clase"],
                "cargado_h": round(datos["cargado"] / 60, 2),
                "registrado_h": round(datos["registrado"] / 60, 2),
                "gemelo_h": round(datos["gemelo"] / 60, 2),
                "pico": None if datos["pico"] is None else round(datos["pico"], 2),
                "alarma": reloj(datos["alarma"]) if datos["alarma"] else None}

    diez = next(p for p in pesos if p["minutos_por_punto"] == MINUTOS_POR_PUNTO)
    uno = next(p for p in pesos if p["minutos_por_punto"] == 1)
    # El motor SQL del módulo 8, pesado igual que esto en src/site/make_sample.py,
    # para comparar las dos maneras de llevar datos al lector: precalcular las
    # respuestas o llevarle el motor para que pregunte lo que quiera.
    muestra = PROJECT / "results" / "sample.json"
    motor_mb = (json.load(io.open(muestra, encoding="utf-8")).get("motor_mb")
                if muestra.exists() else None)
    payload = {
        "dias": len(registros),
        "juzgables": len(por_dia),
        "umbral": umbral,
        "suelo": suelo,
        "minutos_por_punto": MINUTOS_POR_PUNTO,
        "puntos_por_dia": PUNTOS,
        "por_clase": cuenta,
        "pesos": pesos,
        "ficheros": ficheros,
        # Las comparaciones que la lección hace en prosa, calculadas aquí.
        "acumulado_contra_tramos_a_10_min": round(
            diez["acumulado"]["kb_red"] / diez["tramos"]["kb_red"], 1),
        "tramos_a_1_min_pesan_menos_que_acumulado_a_10": (
            uno["tramos"]["kb_red"] < diez["acumulado"]["kb_red"]),
        "ahorro_de_los_caracteres_kb": round(
            diez["tramos"]["kb_red"] - diez["caracteres"]["kb_red"], 1),
        "redondeo_por_tramo_peor_min": round(peor_por_tramo, 1),
        "redondeo_acumulado_peor_min": round(peor_acumulado, 1),
        "compresion_del_fichero": round(ficheros["es"]["kb"] / ficheros["es"]["kb_red"], 1),
        "motor_mb": motor_mb,
        "motor_contra_panel": (round(motor_mb * 1024 / ficheros["es"]["kb_red"])
                               if motor_mb else None),
        "dia_inicial": resumen(DIA_INICIAL),
        "dias_que_cuentan": [resumen(d) for d in DIAS_QUE_CUENTAN],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que el panel promete, comprobado antes de dejarlo salir.
    #
    #   1. Los días con alarma, los aciertos y las falsas alarmas cuadran con el
    #      veredicto del módulo 28, en sus dos cuentas. Si no cuadran, hay dos
    #      definiciones del mismo día y una de las dos miente.
    fila = next(b for b in principal if b["umbral"] == umbral)
    con_marzo = next(b for b in veredicto["barridos"]["congelado, marzo cuenta"]
                     if b["umbral"] == umbral)
    dias_de_parte = {str(dd) for p in partes for dd in p["dias"]}
    falsas = {d for d in alarmas if d not in dias_de_parte}
    falsas_sin_marzo = {d for d in falsas
                        if not inicio_marzo <= date.fromisoformat(d) <= fin_marzo}
    detectados = sum(1 for p in partes if alarmas_por_parte[p["clave"]])
    comprobaciones = [
        ("días con alarma", len(alarmas), fila["dias_con_alarma"]),
        ("partes detectados", detectados, fila["detectados"]),
        ("falsas alarmas, marzo no cuenta", len(falsas), fila["falsas_alarmas"]),
        ("falsas alarmas, marzo cuenta", len(falsas_sin_marzo),
         con_marzo["falsas_alarmas"]),
    ]
    for nombre, aqui, alli in comprobaciones:
        if aqui != alli:
            raise SystemExit(f"El panel cuenta {aqui} {nombre} y el módulo 28 publica "
                             f"{alli}. Hay dos definiciones del mismo día.")
    #   1b. Y el residual máximo de cada día es el mismo número en los dos sitios.
    #       Con una diezmilésima de holgura: el 28 suma con varios hilos y esto con
    #       uno, y una media sumada en otro orden puede caer al otro lado de un
    #       redondeo. Más que eso ya no es orden de suma, es otra definición.
    serie = {x["dia"]: x["congelado"] for x in veredicto["serie_diaria"]}
    distintos = [d for d, v in por_dia.items()
                 if serie.get(d) is None or abs(round(v["pico"], 4) - serie[d]) > 1.1e-4]
    if distintos:
        raise SystemExit(f"{len(distintos)} días con un residual máximo distinto del que "
                         f"publica el módulo 28, empezando por el {distintos[0]}.")
    #   2. El día con el que abre el panel cuenta la historia solo: la alarma salta
    #      a la hora en que empieza el parte. Es la razón de abrir en él.
    inicial = registros[indices[DIA_INICIAL]]
    empieza = [p["empieza"] for p in inicial["partes"]
               if p["empieza"].date() == inicial["fecha"]]
    if not (inicial["clase"] == "acierto" and empieza and inicial["datos"]["alarma"]
            and empieza[0].hour == inicial["datos"]["alarma"].hour):
        raise SystemExit(f"El {DIA_INICIAL} ya no salta a la hora del parte. El panel "
                         "abre en ese día precisamente por eso: hay que elegir otro.")
    #   3. Y el peso que justifica la escritura elegida. Si los tramos dejan de pesar
    #      claramente menos que el acumulado, la lección publica lo contrario.
    if diez["tramos"]["kb_red"] * 2 > diez["acumulado"]["kb_red"]:
        raise SystemExit("Los tramos ya no pesan ni la mitad que el acumulado. La "
                         "lección 30 publica que la escritura manda sobre la resolución.")
    print("  las cuatro cuentas cuadran con el módulo 28, y el 5 de junio sigue "
          "saltando a la hora del parte")


if __name__ == "__main__":
    main()
