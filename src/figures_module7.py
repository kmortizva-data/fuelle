"""Las dos figuras del módulo 7: el formato y, dentro del formato, la columna.

La primera compara CSV con Parquet en tres preguntas distintas, y lo que enseña
no es que Parquet gane: es que gana **menos** cuanto más columnas hay que leer.
Esa pendiente es la definición de columnar, dibujada.

La segunda es la que de verdad explica el peso de un Parquet. Cada columna con
lo que ocupa dentro del fichero, leído de la propia contabilidad del fichero, y
al lado cuántos valores distintos tiene. Las dos que no repiten nunca se comen
el fichero; las ocho digitales, que solo valen cero o uno, no pesan nada.

Correr:  .venv\\Scripts\\python.exe src\\figures_module7.py
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
DATOS = PROJECT / "results" / "m07_formats.json"

PREGUNTAS = {
    "contar_filas": "contar filas",
    "una_columna": "una columna",
    "siete_columnas": "siete columnas",
}


def csv_contra_parquet(datos: dict) -> str:
    name = "fig_m7_csv_vs_parquet"
    preguntas = datos["preguntas"]
    etiquetas = [PREGUNTAS[p["pregunta"]] for p in preguntas]
    csv = [p["csv_s"] for p in preguntas]
    parquet = [p["parquet_s"] for p in preguntas]
    veces = [p["veces"] for p in preguntas]
    x = np.arange(len(preguntas))

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=7)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(8.6, 3.2))
            ax.bar(x - 0.19, csv, width=0.34, color=c["ink_faint"], zorder=3, label="CSV")
            ax.bar(x + 0.19, parquet, width=0.34, color=c["accent"], zorder=3,
                   label="Parquet")
            ax.set_yscale("log")
            ax.set_ylabel("segundos (escala logarítmica)")
            ax.set_xticks(x)
            ax.set_xticklabels(etiquetas)
            ax.grid(axis="y", zorder=0)
            ax.legend(frameon=False, fontsize=8, loc="upper left")

            for i, (a, b, v) in enumerate(zip(csv, parquet, veces)):
                if v:
                    ax.annotate(f"{v:.0f} veces", xy=(i, max(a, b)), xytext=(0, 26),
                                textcoords="offset points", ha="center",
                                fontsize=8, color=c["ink_soft"])
            ax.set_ylim(min(parquet) * 0.4, max(csv) * 6)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def filas_contra_columnas(datos: dict) -> str:
    name = "fig_m7_filas_vs_columnas"
    pesos = datos["pesos_por_columna"]
    nombres = [p["columna"] for p in pesos]
    kb = [p["kb"] for p in pesos]
    distintos = [p["valores_distintos"] for p in pesos]
    y = np.arange(len(pesos))

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=7)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 4.2), sharey=True,
                                           gridspec_kw={"wspace": 0.11})

            izq.barh(y, kb, height=0.62, color=c["accent"], zorder=3)
            izq.set_xlabel("KB que ocupa la columna dentro del fichero")
            izq.invert_yaxis()
            izq.set_yticks(y)
            izq.set_yticklabels(nombres)
            izq.grid(axis="x", zorder=0)
            for i, v in zip(y, kb):
                izq.annotate(es(v), xy=(v, i), xytext=(4, 0),
                             textcoords="offset points", va="center",
                             fontsize=8, color=c["ink_soft"])
            izq.set_xlim(0, max(kb) * 1.18)

            der.barh(y, distintos, height=0.62, color=c["ink_faint"], zorder=3)
            der.set_xscale("log")
            der.set_xlabel("valores distintos en la columna (escala logarítmica)")
            der.grid(axis="x", zorder=0)
            for i, v in zip(y, distintos):
                der.annotate(es(v), xy=(v, i), xytext=(4, 0),
                             textcoords="offset points", va="center",
                             fontsize=8, color=c["ink_soft"])
            der.set_xlim(1, max(distintos) * 9)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m07_formats.json. "
                         "Corre src/transform/benchmark_formats.py")

    datos = json.loads(io.open(DATOS, encoding="utf-8").read())
    FIGURES.mkdir(exist_ok=True)
    nombres = [csv_contra_parquet(datos), filas_contra_columnas(datos)]
    guardar_huellas(nombres)

    pesada = datos["pesos_por_columna"][0]
    print(f"  la columna más pesada es {pesada['columna']}, "
          f"{pesada['por_ciento_del_fichero']} % del fichero "
          f"con {pesada['valores_distintos']:,} valores distintos")


if __name__ == "__main__":
    main()
