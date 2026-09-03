"""The two figures of the verdict. Module 28.

`fig_m28_cuatro_averias` puts each event under its own magnifying glass: ten days
before and after, the two indicators, and the threshold that the sweep picked.
Five panels and not four, because the twelve undocumented days of March are the
fifth event and hiding them would be choosing the evidence.

What the panels show is the module's honest verdict in one picture. **The alarm
goes up on the day**, not before it. Detection works and prediction barely does.

`fig_m28_antelacion_vs_falsas` is the trade off, with the rival on the same axes.
Every threshold of the sweep is a point: how many events it catches against how
many false alarms a month it costs. The alarm the machine already carries is one
more point, and where it lands is the whole argument.

Run:  .venv\\Scripts\\python.exe src\\figures_module28.py
"""

from __future__ import annotations

import datetime
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                           guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m28_veredicto.json"
RESULTS = PROJECT / "results" / "m28_figuras.json"

DIAS_ALREDEDOR = 10

# El barrido que se dibuja: el congelado sin contar marzo, que es la cuenta
# conservadora. La otra sale en la tabla de la lección.
BARRIDO = "congelado, marzo no cuenta"


def alrededor(serie: list[dict], centro: datetime.date) -> list[dict]:
    return [x for x in serie
            if abs((datetime.date.fromisoformat(x["dia"]) - centro).days)
            <= DIAS_ALREDEDOR]


def sucesos(d: dict) -> list[dict]:
    """Los cuatro partes más marzo, con su primer día, su largo y su etiqueta.

    El fichero de partes trae **dos filas llamadas «#1»**, y se copian tal cual
    porque el original manda. Para poder hablar de ellas por separado, el curso
    llama #1b a la segunda, y aquí se numeran igual.
    """
    fuera, vistos = [], {}
    for p in d["partes"]:
        vistos[p["nr"]] = vistos.get(p["nr"], 0) + 1
        sufijo = "" if vistos[p["nr"]] == 1 else "b"
        fuera.append({"nombre": p["nr"] + sufijo, "empieza": p["empieza"][:10],
                      "largo": len(p["dias"]), "documentado": True})
    ini = datetime.date.fromisoformat(d["evento_de_marzo"][0])
    fin = datetime.date.fromisoformat(d["evento_de_marzo"][1])
    fuera.append({"nombre": "marzo", "empieza": d["evento_de_marzo"][0],
                  "largo": (fin - ini).days + 1, "documentado": False})
    return sorted(fuera, key=lambda s: s["empieza"])


def lupa(d: dict, umbral: float, col: dict):
    """Los cinco sucesos, cada uno con sus diez días a cada lado."""
    ss = sucesos(d)
    fig, ejes = plt.subplots(1, len(ss), figsize=(9.4, 2.9), sharey=True,
                             gridspec_kw={"wspace": 0.10})
    for ax, s in zip(ejes, ss):
        centro = datetime.date.fromisoformat(s["empieza"])
        trozo = alrededor(d["serie_diaria"], centro)
        x = [(datetime.date.fromisoformat(t["dia"]) - centro).days for t in trozo]
        ax.axhline(umbral, color=col["simulated"], linewidth=1.1, linestyle="--",
                   zorder=3)
        # La banda dura lo que dura el suceso, y marzo dura doce días. Con la
        # banda de un día, el panel de marzo decía que fue cosa de una tarde.
        ax.axvspan(-0.4, max(s["largo"] - 1, 0.4), color=col["accent"],
                   alpha=0.20, zorder=1)
        ax.plot(x, [t["congelado"] for t in trozo], color=col["measured"],
                linewidth=1.5, marker="o", markersize=2.2, zorder=4)
        titulo = s["nombre"] if s["documentado"] else "marzo, sin parte"
        ax.set_title(titulo, fontsize=9, color=col["ink_soft"], pad=7)
        ax.set_xlabel("días")
        ax.set_xlim(-DIAS_ALREDEDOR, DIAS_ALREDEDOR)
        # Sin esto, el −10 de un panel y el 10 del vecino se tocan.
        ax.set_xticks([-DIAS_ALREDEDOR, 0, DIAS_ALREDEDOR])
        ax.grid(axis="y", zorder=0)
    ejes[0].set_ylabel("residual del día, bar/min")
    fig.tight_layout(pad=0.6)
    return fig


def intercambio(d: dict, col: dict):
    """Cuántos sucesos pilla cada umbral contra lo que cuesta, con el rival."""
    barrido = d["barridos"][BARRIDO]
    lps = d["rival_instalado"]
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.plot([b["falsas_por_mes"] for b in barrido],
            [b["detectados"] for b in barrido],
            color=col["measured"], linewidth=1.6, marker="o", markersize=3.4,
            zorder=4, label="el gemelo, umbral a umbral")
    ax.scatter([lps["falsas_por_mes"]], [lps["de_cuatro_partes"]], s=110,
               marker="X", color=col["simulated"], zorder=5,
               label="la alarma que la máquina ya lleva")

    # El punto de operación: el umbral más alto que aún los pilla todos.
    todos = [b for b in barrido if b["detectados"] == b["sucesos"]]
    elegido = max(todos, key=lambda b: b["umbral"])
    ax.scatter([elegido["falsas_por_mes"]], [elegido["detectados"]], s=150,
               facecolors="none", linewidths=1.7, color=col["measured"], zorder=6)
    ax.annotate(f"umbral {es(elegido['umbral'], 2)}",
                xy=(elegido["falsas_por_mes"], elegido["detectados"]), fontsize=8.5,
                color=col["ink_soft"], ha="left", va="top",
                xytext=(9, -4), textcoords="offset points")
    ax.set_xlabel("falsas alarmas por mes")
    ax.set_ylabel("averías detectadas, de cuatro")
    ax.set_ylim(-0.3, 4.5)
    ax.grid(axis="y", zorder=0)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout(pad=0.6)
    return fig, elegido


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Faltan las cifras. Corre src/twin/evaluate.py primero.")
    d = json.load(io.open(DATOS, encoding="utf-8"))

    barrido = d["barridos"][BARRIDO]
    todos = [b for b in barrido if b["detectados"] == b["sucesos"]]
    elegido = max(todos, key=lambda b: b["umbral"])

    nombres = ["fig_m28_cuatro_averias", "fig_m28_antelacion_vs_falsas"]
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        col = colours(theme, module=28)
        with plt.rc_context(_style(theme, col)):
            uno = lupa(d, elegido["umbral"], col)
            dos, _ = intercambio(d, col)
            for nombre, fig in zip(nombres, (uno, dos)):
                target = FIGURES / f"{nombre}.{theme}.png"
                fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
                plt.close(fig)
                print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                      f"{fingerprint(target)}")
    guardar_huellas(nombres)

    lps = d["rival_instalado"]
    payload = {
        "barrido_dibujado": BARRIDO,
        "umbral_elegido": elegido["umbral"],
        "detecta": elegido["detectados"],
        "de": elegido["sucesos"],
        "falsas_por_mes": elegido["falsas_por_mes"],
        "falsas_alarmas": elegido["falsas_alarmas"],
        "dias_con_alarma": elegido["dias_con_alarma"],
        "rival_detecta": lps["de_cuatro_partes"],
        "rival_falsas_por_mes": lps["falsas_por_mes"],
        # Lo que gana el gemelo sobre lo que ya estaba instalado, en las dos
        # cuentas que importan.
        "el_doble_de_averias": round(
            elegido["detectados"] / max(lps["de_cuatro_partes"], 1), 1),
        "la_mitad_de_falsas": round(
            lps["falsas_por_mes"] / max(elegido["falsas_por_mes"], 0.1), 1),
    }
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"  umbral elegido {elegido['umbral']}: {elegido['detectados']} de "
          f"{elegido['sucesos']} con {elegido['falsas_por_mes']} falsas al mes")
    print(f"  la alarma instalada: {lps['de_cuatro_partes']} de 4 con "
          f"{lps['falsas_por_mes']} falsas al mes")


if __name__ == "__main__":
    main()
