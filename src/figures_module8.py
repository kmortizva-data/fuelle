"""La figura del módulo 8: el calendario, con sus dos agujeros.

Un año de datos parece un bloque macizo hasta que se dibuja día a día. Entonces
se ven dos cosas a la vez: dónde salta la alarma de baja presión, y que hay dos
casillas que no existen.

Las casillas ausentes se dibujan con un aspa y no en blanco, porque un blanco se
lee como cero y ahí está justo el error que el módulo enseña a no cometer. Un
día sin datos no es un día tranquilo: es un día del que no se sabe nada.

Correr:  .venv\\Scripts\\python.exe src\\figures_module8.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from figures_theme import FIGURES, _style, colours, fingerprint, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m08_primera_consulta.json"
POR_DIA = PROJECT / "results" / "m04_particiones.json"

MESES = ["feb", "mar", "abr", "may", "jun", "jul", "ago", "sep"]


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m08_primera_consulta.json. "
                         "Corre src/transform/queries_m08.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    faltan = {date.fromisoformat(x) for x in d["dias_que_faltan"]}
    con_datos = {date.fromisoformat(x["dia"]) for x in
                 json.loads(io.open(POR_DIA, encoding="utf-8").read())["dias"]}
    alarmas = {x["dia"]: x["lecturas"] for x in d["alarmas_por_dia"]}

    pico = max(alarmas.values())
    inicio, fin = date(2020, 2, 1), date(2020, 9, 1)
    dias = [inicio + timedelta(days=i) for i in range((fin - inicio).days + 1)]

    # Una rejilla de semanas: filas de siete días, como un calendario de pared.
    filas = 7
    columnas = (len(dias) + filas - 1) // filas

    name = "fig_m08_null_no_es_cero"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=8)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.2, 2.9))

            for i, dia in enumerate(dias):
                x, y = i // filas, i % filas
                if dia in faltan:
                    # El aspa: no hay dato. No es un cero, es una ausencia.
                    ax.plot([x - 0.32, x + 0.32], [y - 0.32, y + 0.32],
                            color=c["ink"], linewidth=1.5, zorder=6)
                    ax.plot([x - 0.32, x + 0.32], [y + 0.32, y - 0.32],
                            color=c["ink"], linewidth=1.5, zorder=6)
                    continue
                if dia not in con_datos:
                    continue
                n = alarmas.get(dia.isoformat(), 0)
                # La intensidad dice cuanto salto la alarma ese dia. Un dia sin
                # alarma se pinta del gris de la rejilla, que no es lo mismo que
                # un dia ausente: ese lleva aspa.
                color = c["rule"] if not n else (c["accent"], min(1.0, 0.28 + n / pico))
                ax.add_patch(plt.Rectangle((x - 0.42, y - 0.42), 0.84, 0.84,
                                           facecolor=color, edgecolor="none", zorder=3))

            for dia in sorted(faltan):
                i = (dia - inicio).days
                ax.annotate(dia.isoformat(), xy=(i // filas, i % filas),
                            xytext=(0, 16), textcoords="offset points",
                            ha="center", fontsize=8, color=c["ink"], zorder=7)

            # Los meses, en el eje de abajo.
            marcas, etiquetas = [], []
            for mes in range(2, 10):
                primero = date(2020, mes, 1)
                if inicio <= primero <= fin:
                    marcas.append((primero - inicio).days // filas)
                    etiquetas.append(MESES[mes - 2])
            ax.set_xticks(marcas)
            ax.set_xticklabels(etiquetas)
            ax.set_yticks([])
            ax.set_xlim(-1, columnas)
            ax.set_ylim(filas - 0.5, -0.5)
            for lado in ("left", "bottom"):
                ax.spines[lado].set_visible(False)
            ax.tick_params(length=0)
            ax.set_xlabel("cada casilla es un día y cuanto más clara más saltó la alarma; "
                          "el aspa es un día que no existe")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {len(dias)} días de calendario, {len(con_datos)} con datos, "
          f"{len(faltan)} ausentes")


if __name__ == "__main__":
    main()
