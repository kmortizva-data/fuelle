"""La figura del módulo 4: las 212 particiones no son 212 días iguales.

«212 carpetas» suena a reparto ordenado, y el reparto no lo es. Un día lleno son
8.640 lecturas y la mayoría de los días no llegan. Dibujarlo por fecha enseña
además que los huecos no están repartidos al azar: hay tramos enteros flojos.

La línea del día lleno va discontinua porque es una referencia y no una medida.
Es la misma regla de forma que separa lo medido de lo simulado en el resto del
curso.

Correr:  .venv\\Scripts\\python.exe src\\figures_module4.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import es, figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m04_particiones.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m04_particiones.json. "
                         "Corre src/ingest/partition_profile.py")

    datos = json.loads(io.open(DATOS, encoding="utf-8").read())
    dias = [date.fromisoformat(d["dia"]) for d in datos["dias"]]
    lecturas = [d["lecturas"] for d in datos["dias"]]
    lleno = datos["lecturas_de_un_dia_lleno"]
    mediana = datos["lecturas_mediana"]

    def dibujar(fig, ax, c):
        ax.bar(dias, lecturas, width=1.0, color=c["accent"], zorder=3, linewidth=0)
        caja = {"facecolor": c["ground"], "edgecolor": "none", "pad": 1.6}

        ax.axhline(lleno, color=c["ink"], linestyle="--", linewidth=1.1, zorder=5)
        ax.annotate(f"un día lleno, {es(lleno)} lecturas",
                    xy=(dias[2], lleno), xytext=(0, 6), textcoords="offset points",
                    fontsize=8, color=c["ink"], zorder=6)
        ax.axhline(mediana, color=c["ink"], linestyle=":", linewidth=1.1, zorder=5)
        # Con fondo propio: la línea de la mediana cruza por encima de las
        # barras y sin caja la etiqueta se pierde dentro de ellas.
        ax.annotate(f"mediana, {es(mediana)}",
                    xy=(dias[-1], mediana), xytext=(-4, 6), textcoords="offset points",
                    ha="right", fontsize=8, color=c["ink"], bbox=caja, zorder=6)
        ax.set_ylabel("lecturas en la partición")
        ax.set_ylim(0, lleno * 1.12)
        ax.grid(axis="y", zorder=0)
        ax.set_xlim(dias[0], dias[-1])

    figura("fig_m4_bronce_particiones", dibujar, ancho=9.2, alto=3.0, module=4)
    guardar_huellas(["fig_m4_bronce_particiones"])
    print(f"  {datos['particiones']} particiones, mediana {datos['lecturas_mediana']:,}, "
          f"{datos['dias_completos']} por encima del 90 %")


if __name__ == "__main__":
    main()
