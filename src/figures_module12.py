"""Las dos figuras del módulo 12: los tres cruces y el que multiplica.

La primera cuenta cuántas filas devuelve el mismo cruce escrito de tres formas.
Un diagrama de conjuntos explica los tipos de JOIN en abstracto; estos tres
números los explican sobre los datos del compresor, que es lo que hace este
curso.

La segunda dibuja el fallo con nombre y apellidos: los cuatro partes de avería a
la izquierda y las seis filas que salen al cruzarlos por su número. Las dos
líneas que se abren son las dos filas numeradas «#1», que es una errata real del
fichero y no un ejemplo inventado.

Correr:  .venv\\Scripts\\python.exe src\\figures_module12.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                            guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m12_join.json"

QUE_HACE = {
    "INNER JOIN": "solo las lecturas\ncon avería",
    "LEFT JOIN": "todas las lecturas,\ncon avería o sin ella",
    "CROSS JOIN": "cada lectura con\ncada parte",
}


def tipos_de_join(d: dict) -> str:
    name = "fig_m12_tipos_de_join"
    tipos = d["tipos_de_join"]
    nombres = [t["tipo"] for t in tipos]
    filas = [t["filas"] for t in tipos]
    y = np.arange(len(tipos))

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=12)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.0, 2.8))
            ax.barh(y, filas, height=0.5, color=c["accent"], zorder=3)
            ax.set_xscale("log")
            ax.invert_yaxis()
            ax.set_yticks(y)
            ax.set_yticklabels(nombres)
            ax.grid(axis="x", zorder=0)

            for i, (n, f) in enumerate(zip(nombres, filas)):
                ax.annotate(f"{es(f)}   {QUE_HACE[n]}".replace("\n", "  "),
                            xy=(f, i), xytext=(7, 0), textcoords="offset points",
                            va="center", fontsize=8.5, color=c["ink_soft"])
            # La referencia: cuántas lecturas había antes de cruzar nada.
            ax.axvline(d["lecturas"], color=c["ink"], linestyle="--",
                       linewidth=1.1, zorder=5)
            ax.annotate(f"las {es(d['lecturas'])} lecturas de partida",
                        xy=(d["lecturas"], 1), xycoords=("data", "axes fraction"),
                        xytext=(-6, -12), textcoords="offset points", ha="right",
                        fontsize=8, color=c["ink"], zorder=6)
            ax.set_xlim(min(filas) * 0.5, max(filas) * 60)
            ax.set_xlabel("filas que devuelve el cruce (escala logarítmica)")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def join_que_multiplica(d: dict) -> str:
    name = "fig_m12_join_que_multiplica"
    partes = d["por_averia"]
    izquierda = [f"{p['nr']}   {p['desde']}" for p in partes]
    repetido = {x["nr"] for x in d["numeros_repetidos"]}

    # A qué filas del resultado va a parar cada parte al cruzar por nr.
    destino, salida = [], []
    for i, p in enumerate(partes):
        hermanos = [j for j, q in enumerate(partes) if q["nr"] == p["nr"]]
        for j in hermanos:
            destino.append((i, len(salida)))
            salida.append(f"{p['nr']} con {partes[j]['desde']}")

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=12)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.0, 3.4))

            for i, etiqueta in enumerate(izquierda):
                mal = partes[i]["nr"] in repetido
                ax.annotate(etiqueta, xy=(0, i), ha="left", va="center",
                            fontsize=9, family="monospace",
                            color=c["accent"] if mal else c["ink"], zorder=5)
            for j, etiqueta in enumerate(salida):
                ax.annotate(etiqueta, xy=(1, j * len(partes) / len(salida)),
                            ha="left", va="center", fontsize=9, family="monospace",
                            color=c["ink_soft"], zorder=5)
            for i, j in destino:
                doble = partes[i]["nr"] in repetido
                ax.plot([0.28, 0.97], [i, j * len(partes) / len(salida)],
                        color=c["accent"] if doble else c["rule"],
                        linewidth=1.6 if doble else 1.0, zorder=3)

            ax.annotate(f"{len(partes)} partes de avería", xy=(0, -0.9),
                        fontsize=9, color=c["ink_soft"])
            ax.annotate(f"{len(salida)} filas al cruzar por  nr", xy=(1, -0.9),
                        fontsize=9, color=c["ink_soft"])
            ax.set_xlim(-0.05, 1.62)
            ax.set_ylim(len(partes) - 0.4, -1.4)
            ax.axis("off")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m12_join.json. Corre src/transform/queries_m12.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    FIGURES.mkdir(exist_ok=True)
    guardar_huellas([tipos_de_join(d), join_que_multiplica(d)])
    print(f"  {d['partes']} partes se convierten en {d['filas_cruzando_por_nr']} "
          f"al cruzar por nr")


if __name__ == "__main__":
    main()
