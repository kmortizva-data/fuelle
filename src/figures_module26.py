"""The two figures of module 26: what the search finds, and how it holds up.

`fig_m26_ajuste` is the point of the module. Three error surfaces over the same
grid of two parameters, and what changes between them is only **what the search
was told to match**:

  - the duty cycle alone      -> a valley. Every pair with the right ratio ties
  - the starts per hour alone -> another valley, crossing the first
  - both at once              -> one point, where they cross

The measured parameters go on all three, so you can see them land in the valley
in the first two and next to the minimum in the third. That is the result: two
numbers measured with no fitting fall where the fit ends up.

`fig_m26_gemelo_vs_real_sano` is the double trace over a healthy week, and it
exists to show what an 8 per cent disagreement between measuring and fitting
looks like when you draw it, which is almost nothing.

Run:  .venv\\Scripts\\python.exe src\\figures_module26.py
"""

from __future__ import annotations

import datetime
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                           guardar_huellas)
from twin.model import Deposito, mide  # noqa: E402
from twin.simulate import avanza  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
AJUSTE = PROJECT / "results" / "m26_calibrar.json"
VENTANA = PROJECT / "results" / "m26_ventana.json"
RESULTS = PROJECT / "results" / "m26_figuras.json"

# Una semana sana entera, la del 16 al 22 de febrero. Lleva cuatro días completos
# de los siete y ninguno de los huecos gordos, y sobre todo **no toca marzo**.
SEMANA = ("2020-02-16", "2020-02-22")
PASO = 5 / 60           # el que salió del módulo 25


# El registro va a una lectura cada diez segundos y el gemelo corre a `PASO`, que
# desde el módulo 25 es más fino. Si se le dan tantos pasos como lecturas, el
# gemelo vive **la mitad del reloj** y se queda corto sin que sea culpa suya.
SEGUNDOS_POR_LECTURA = 10


def traza_del_gemelo(dep, lecturas: int, paso: float) -> list[float]:
    """Los minutos cargando del gemelo, en el mismo reloj que las lecturas."""
    minutos = lecturas * SEGUNDOS_POR_LECTURA / 60
    trabajo = avanza(dep, dep.consumo, minutos, paso)["trabajo"]
    cada = SEGUNDOS_POR_LECTURA / 60 / paso
    return [trabajo[min(int(round(i * cada)), len(trabajo) - 1)]
            for i in range(lecturas)]


def real(desde: str, hasta: str) -> list[float]:
    """Los minutos cargando acumulados de la máquina, lectura a lectura."""
    con = duckdb.connect()
    filas = con.sql(f"""
        SELECT sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                   OVER (ORDER BY timestamp) / 6.0 AS acumulado
        FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
        WHERE medido AND day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        ORDER BY timestamp
    """).fetchall()
    con.close()
    return [float(f[0]) for f in filas]


def superficies(ajuste: dict, theme: str, col: dict) -> None:
    """Las tres superficies de error, una al lado de otra."""
    E, C = ajuste["entregas"], ajuste["consumos"]
    medido = ajuste["medido"]
    titulos = {"solo la carga": "ajustando la carga",
               "solo los arranques": "ajustando los arranques",
               "las dos cosas": "ajustando las dos cosas"}

    # Un degradado del acento del módulo: oscuro donde el error es pequeño, para
    # que el valle se lea como un surco y no como una cresta.
    mapa = LinearSegmentedColormap.from_list(
        "error", [col["accent"], col["ground"]])

    fig, ejes = plt.subplots(1, 3, figsize=(9.4, 3.1), sharey=True,
                             gridspec_kw={"wspace": 0.08})
    for ax, (nombre, titulo) in zip(ejes, titulos.items()):
        s = ajuste["superficies"][nombre]
        mejor = ajuste["mejores"][nombre]
        # La escala se recorta al percentil bajo: por encima ya es todo malo y
        # pintarlo entero aplasta el valle, que es lo que hay que ver.
        planos = sorted(v for fila in s for v in fila if v is not None)
        tope = planos[len(planos) // 5]
        ax.pcolormesh([*C, C[-1] + (C[1] - C[0])],
                      [*E, E[-1] + (E[1] - E[0])],
                      [[tope if v is None else min(v, tope) for v in fila]
                       for fila in s],
                      cmap=mapa, vmin=0, vmax=tope, zorder=1)
        # Los puntos que empatan con el mejor: eso es el valle, dibujado.
        atados = [(C[j], E[i]) for i, fila in enumerate(s)
                  for j, v in enumerate(fila)
                  if v is not None and v <= mejor["error"] + 0.002]
        ax.scatter([c for c, _ in atados], [e for _, e in atados], s=7,
                   color=col["simulated"], alpha=0.75, zorder=3,
                   label="empatan con el mejor")
        # El mejor punto, con anillo, porque en el panel de la derecha es uno
        # solo y hay que verlo: ahí está la diferencia con los otros dos.
        ax.scatter([mejor["consumo"]], [mejor["entrega"]], s=90, marker="o",
                   facecolors="none", linewidths=1.6, color=col["simulated"],
                   zorder=5, label="el mejor")
        ax.scatter([medido["consumo"]], [medido["entrega"]], s=64, marker="+",
                   linewidths=2.0, color=col["measured"], zorder=6,
                   label="lo que se midió")
        ax.set_title(titulo, fontsize=9, color=col["ink_soft"], pad=8)
        ax.set_xlabel("consumo, bar/min")
        ax.set_xlim(C[0], C[-1])
        ax.set_ylim(E[0], E[-1])
    ejes[0].set_ylabel("entrega, bar/min")
    ejes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(pad=0.6)
    return fig


def doble_trazo(medido: list[float], simulado: list[float], col: dict):
    """La semana sana, con el gemelo encima."""
    fig, ax = plt.subplots(figsize=(9.2, 3.0))
    # El eje es el reloj del REGISTRO, no el paso del gemelo. Los dos son
    # distintos desde el módulo 25 y confundirlos encoge el eje a la mitad.
    dias = [i * SEGUNDOS_POR_LECTURA / 60 / 1440 for i in range(len(medido))]
    ax.fill_between(dias, simulado, medido, color=col["accent"], alpha=0.16,
                    zorder=2)
    ax.plot(dias, medido, color=col["measured"], linewidth=1.8, zorder=4,
            label="la máquina")
    ax.plot(dias, simulado, color=col["simulated"], linewidth=1.8, zorder=4,
            linestyle="--", label="el gemelo")
    ax.set_xlabel("días de registro de la semana")
    ax.set_ylabel("minutos cargando, acumulados")
    ax.set_xlim(0, dias[-1])
    ax.grid(axis="y", zorder=0)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout(pad=0.6)
    return fig


def ventana_sucia(v: dict, col: dict):
    """Las cuatro señales de la ventana vieja, y los doce días que la ensucian.

    Cuatro paneles y no uno, porque el argumento **es** que son cuatro
    instrumentos distintos moviéndose a la vez. Con uno solo siempre queda la
    duda de si es el sensor; con cuatro, no.
    """
    dias = v["dias"]
    x = [datetime.date.fromisoformat(d["dia"]) for d in dias]
    series = (("carga", "ciclo de trabajo", None),
              ("arranques", "arranques por hora", None),
              ("aceite", "aceite, °C", None),
              ("corriente", "corriente del motor, A", None))
    ini = datetime.date.fromisoformat(v["evento"][0])
    fin = datetime.date.fromisoformat(v["evento"][1])
    corte = datetime.date.fromisoformat(v["ventana_nueva"][1])

    fig, ejes = plt.subplots(4, 1, figsize=(9.2, 5.2), sharex=True,
                             gridspec_kw={"hspace": 0.18})
    for ax, (clave, etiqueta, _) in zip(ejes, series):
        ax.axvspan(ini, fin, color=col["accent"], alpha=0.18, zorder=1)
        ax.plot(x, [d[clave] for d in dias], color=col["measured"], linewidth=1.5,
                marker="o", markersize=2.4, zorder=3)
        ax.set_ylabel(etiqueta, fontsize=8)
        ax.grid(axis="y", zorder=0)
    # Las dos ventanas de calibración, la de antes y la de ahora, para que se
    # vea de un golpe que la vieja se tragaba el evento entero.
    viejo = datetime.date.fromisoformat(v["ventana_vieja"][1])
    for ax in ejes:
        for x0, estilo in ((corte, ":"), (viejo, "--")):
            ax.axvline(x0, color=col["simulated"], linewidth=1.3, linestyle=estilo,
                       zorder=4)
    arriba = ejes[0].get_ylim()[1]
    ejes[0].annotate("acaba la\nventana de ahora", xy=(corte, arriba), fontsize=8,
                     color=col["ink_soft"], ha="right", va="top",
                     xytext=(-5, -3), textcoords="offset points")
    ejes[0].annotate("acababa la\nde antes", xy=(viejo, arriba), fontsize=8,
                     color=col["ink_soft"], ha="left", va="top",
                     xytext=(5, -3), textcoords="offset points")
    ejes[-1].set_xlabel("febrero y marzo de 2020")
    fig.tight_layout(pad=0.6)
    return fig


def main() -> None:
    if not AJUSTE.exists():
        raise SystemExit("Falta el ajuste. Corre src/twin/calibrate.py primero.")
    ajuste = json.load(io.open(AJUSTE, encoding="utf-8"))
    if not VENTANA.exists():
        raise SystemExit("Falta la comprobación de la ventana. Corre "
                         "src/twin/ventana_sana.py primero.")
    ventana = json.load(io.open(VENTANA, encoding="utf-8"))
    dep, _ = mide()

    medido = real(*SEMANA)
    simulado = traza_del_gemelo(dep, len(medido), PASO)
    n = len(medido)

    # Y el gemelo con los parámetros del ajuste, para poder decir cuánto se
    # separan de verdad las dos formas de conseguirlos.
    a = ajuste["ajustado"]
    dep_ajustado = Deposito(arranca=dep.arranca, para=dep.para,
                            llena=a["entrega"] - a["consumo"], consumo=a["consumo"])
    con_ajuste = traza_del_gemelo(dep_ajustado, n, PASO)

    FIGURES.mkdir(exist_ok=True)
    nombres = ["fig_m26_ajuste", "fig_m26_gemelo_vs_real_sano",
               "fig_m26_ventana_sucia"]
    for theme in ("claro", "oscuro"):
        col = colours(theme, module=26)
        with plt.rc_context(_style(theme, col)):
            for nombre, fig in zip(nombres, (superficies(ajuste, theme, col),
                                             doble_trazo(medido, simulado, col),
                                             ventana_sucia(ventana, col))):
                target = FIGURES / f"{nombre}.{theme}.png"
                fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
                plt.close(fig)
                print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                      f"{fingerprint(target)}")
    guardar_huellas(nombres)

    payload = {
        "semana": list(SEMANA),
        "paso_s": round(PASO * 60, 1),
        "minutos_de_la_maquina": round(medido[-1], 1),
        "minutos_del_gemelo_medido": round(simulado[-1], 1),
        "minutos_del_gemelo_ajustado": round(con_ajuste[-1], 1),
        "hueco_del_medido": round(medido[-1] - simulado[-1], 1),
        "hueco_del_ajustado": round(medido[-1] - con_ajuste[-1], 1),
        # Lo que separa a las dos formas de sacar los parámetros, dibujado sobre
        # una semana: es la cifra que dice si la diferencia importa o no.
        "se_separan_entre_ellos": round(abs(simulado[-1] - con_ajuste[-1]), 1),
        # Y en tanto por ciento del trabajo de la máquina, que es lo que dice
        # si un 7,8 % en los parámetros es mucho o es nada.
        "se_separan_pct": round(
            abs(simulado[-1] - con_ajuste[-1]) / medido[-1] * 100, 1),
    }
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  la semana del {SEMANA[0]} al {SEMANA[1]}, sobre lo medido:")
    print(f"    la máquina cargó          {payload['minutos_de_la_maquina']} min")
    print(f"    el gemelo medido          {payload['minutos_del_gemelo_medido']}")
    print(f"    el gemelo ajustado        {payload['minutos_del_gemelo_ajustado']}")
    print(f"    y entre ellos dos se llevan {es(payload['se_separan_entre_ellos'], 1)} min")


if __name__ == "__main__":
    main()
