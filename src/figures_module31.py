"""The figure of module 31: the arc of the project, one measured number per stage.

From a 208 MB text file to one sentence. Each stage shows the number it leaves
behind, and **not one of them is typed here**: every value is read from the
`results/` file of the module that measured it, so a figure that closes the
course cannot quietly disagree with the course.

Run:  .venv\\Scripts\\python.exe src\\figures_module31.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import es, figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT / "results"

NOMBRE = "fig_m31_arco_del_proyecto"


def lee(nombre: str) -> dict:
    return json.loads(io.open(RESULTS / f"{nombre}.json", encoding="utf-8").read())


def etapas() -> list[tuple[str, str, str]]:
    """Las ocho etapas, con la cifra que mide cada una y de dónde sale."""
    m01, bronce, m14 = lee("m01_raw"), lee("bronze"), lee("m14_plata")
    m17, m19 = lee("m17_dbt"), lee("m19_postgres")
    m27, m28 = lee("m27_residual"), lee("m28_veredicto")
    # Los números del gemelo se cuentan en su propia clase, no aquí: si algún día
    # el depósito necesitara un quinto parámetro, la figura lo diría sola.
    import dataclasses

    from twin.model import Deposito

    parametros = len(dataclasses.fields(Deposito))
    principal = m28["barridos"]["congelado, marzo no cuenta"]
    umbral = max(b["umbral"] for b in principal if b["detectados"] == b["sucesos"])
    fila = next(b for b in principal if b["umbral"] == umbral)
    # Las capas van con artículo («el bronce», «la plata», «el oro») y no sueltas:
    # `plata` y `oro` sueltas son nombres de tabla, y la traducción de figuras las
    # deja en español a propósito. Con artículo son prosa, y se traducen.
    return [
        ("el fichero", f"{es(m01['size_mb'], 1)} MB", "de texto"),
        ("el bronce", f"{es(bronce['size_mb'], 2)} MB", f"{es(bronce['partitions'])} días"),
        ("la plata", es(m14["filas_plata"]), "filas en rejilla"),
        ("el oro", es(m17["nodos_del_grafo"]), "nodos con dbt"),
        ("PostgreSQL", f"{es(m19['mb_en_el_servidor'], 1)} MB",
         f"{es(m19['veces_mas_disco_el_servidor'], 1)} veces"),
        ("el gemelo", es(parametros), "números medidos"),
        ("el residual", es(m27["suelo"]["maximo"], 2), "bar/min de suelo"),
        ("el veredicto", f"{fila['detectados']} de {fila['sucesos']}",
         f"{es(fila['falsas_por_mes'], 1)} falsas/mes"),
    ]


def main() -> None:
    pasos = etapas()

    def dibujar(fig, ax, c):
        ancho, hueco = 1.0, 0.28
        for i, (nombre, cifra, pie) in enumerate(pasos):
            x = i * (ancho + hueco)
            ultimo = i == len(pasos) - 1
            borde = c["accent"] if ultimo else c["ink_faint"]
            ax.add_patch(plt_rect(ax, x, 0, ancho, 1, c["panel"], borde, 2 if ultimo else 1))
            ax.text(x + ancho / 2, 0.83, nombre, ha="center", va="center", fontsize=7.4,
                    color=c["ink_soft"] if not ultimo else c["accent"])
            ax.text(x + ancho / 2, 0.52, cifra, ha="center", va="center", fontsize=11.5,
                    color=c["ink"] if not ultimo else c["accent"], fontweight="bold")
            ax.text(x + ancho / 2, 0.22, pie, ha="center", va="center", fontsize=6.8,
                    color=c["ink_faint"])
            if not ultimo:
                medio = x + ancho + hueco / 2
                ax.annotate("", xy=(medio + 0.06, 0.5), xytext=(medio - 0.06, 0.5),
                            arrowprops={"arrowstyle": "-|>", "color": c["ink_faint"],
                                        "linewidth": 0.9})
        ax.set_xlim(-0.12, len(pasos) * (ancho + hueco) - hueco + 0.12)
        ax.set_ylim(-0.06, 1.06)
        ax.axis("off")

    figura(NOMBRE, dibujar, ancho=9.4, alto=1.55, module=31)
    guardar_huellas([NOMBRE])


def plt_rect(ax, x, y, w, h, relleno, borde, grosor):
    """Un rectángulo de caja, con el mismo aire que las del curso."""
    from matplotlib.patches import FancyBboxPatch

    return FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.04",
                          linewidth=grosor, edgecolor=borde, facecolor=relleno,
                          mutation_aspect=1, zorder=2)


if __name__ == "__main__":
    main()
