"""La figura del módulo 29: el curso entero como un solo grafo, leído de Dagster.

Es la regla del módulo 17 un paso más allá. Allí el mapa del oro lo dibujaba dbt
desde su manifest; aquí lo dibuja Dagster desde `definitions.py`, y abarca todo:
el CSV, el lago, el oro de dbt, el gemelo y PostgreSQL. Ni un nodo ni una flecha
están escritos en este fichero. Si mañana alguien añade un activo, la figura lo
tendrá sin tocar una línea.

La columna de cada nodo es su profundidad: cuántos saltos hay desde lo crudo. Es
el mismo cálculo con el que Dagster decide qué construir antes, así que leer la
figura de izquierda a derecha es leer el orden de una reconstrucción entera.

El número en círculo son las comprobaciones que Dagster corre al terminar un
activo: las once pruebas de dbt, el contrato del módulo 16 sobre la plata y la
restauración de la copia del módulo 22.

Correr:  .venv\\Scripts\\python.exe src\\figures_module29.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dagster as dg  # noqa: E402

from figures_theme import figura, guardar_huellas  # noqa: E402
from orchestration.definitions import DIAS, defs  # noqa: E402

GRUPOS = ("crudo", "lago", "lecciones", "gemelo", "servidor")


def main() -> None:
    grafo = defs.resolve_asset_graph()
    claves = list(grafo.get_all_asset_keys())
    nodo = {k: grafo.get(k) for k in claves}
    padres = {k: list(nodo[k].parent_keys) for k in claves}
    aristas = [(p, k) for k in claves for p in padres[k]]
    pruebas = Counter(c.asset_key for c in grafo.asset_check_keys)

    nivel: dict = {}

    def calcula(k) -> int:
        if k not in nivel:
            nivel[k] = 0 if not padres[k] else 1 + max(calcula(p) for p in padres[k])
        return nivel[k]

    for k in claves:
        calcula(k)

    # Una columna por profundidad, y dentro de ella por grupo y por nombre. El
    # desempate existe para que la figura no cambie sin que cambie el proyecto.
    columnas: dict[int, list] = {}
    for k in sorted(claves, key=lambda k: (GRUPOS.index(nodo[k].group_name),
                                           k.to_user_string())):
        columnas.setdefault(nivel[k], []).append(k)
    alto_max = max(len(c) for c in columnas.values())
    paso_x, paso_y = 1.42, 0.78
    sitio = {}
    for x, ks in columnas.items():
        hueco = (alto_max - len(ks)) / 2
        for y, k in enumerate(ks):
            sitio[k] = (x * paso_x, (hueco + y) * paso_y)

    dias = len(DIAS.get_partition_keys())
    # Los reintentos también se leen, de la política que declara cada activo.
    reintentos = {k: a.op.retry_policy.max_retries
                  for a in defs.assets if isinstance(a, dg.AssetsDefinition)
                  and a.op.retry_policy is not None for k in a.keys}

    def rotulo(k) -> str:
        # La clave tal como la enseña Dagster, partida en la barra para que quepa.
        # Son identificadores del código, así que van igual en las dos ediciones.
        return "/\n".join(k.path)

    def dibujar(fig, ax, c) -> None:
        import matplotlib.patches as mpatches

        borde = {"crudo": c["ink_faint"], "lago": c["measured"], "lecciones": c["ink_faint"],
                 "gemelo": c["simulated"], "servidor": c["ink_soft"]}
        ancho, alto = 1.16, 0.5

        for a, b in aristas:
            (xa, ya), (xb, yb) = sitio[a], sitio[b]
            ax.annotate(
                "", xy=(xb - ancho / 2, yb), xytext=(xa + ancho / 2, ya),
                arrowprops=dict(arrowstyle="-|>", color=c["ink_faint"], linewidth=0.8,
                                alpha=0.55, shrinkA=2, shrinkB=2,
                                connectionstyle="arc3,rad=0.06"),
                zorder=2)

        for k, (x, y) in sitio.items():
            grupo = nodo[k].group_name
            # Lo crudo va con borde discontinuo: existe, pero aquí no se construye.
            ax.add_patch(mpatches.FancyBboxPatch(
                (x - ancho / 2, y - alto / 2), ancho, alto,
                boxstyle="round,pad=0,rounding_size=0.05", facecolor=c["panel"],
                edgecolor=borde[grupo], linewidth=1.2,
                linestyle=(0, (3, 2)) if grupo == "crudo" else "solid", zorder=4))
            ax.text(x, y, rotulo(k), ha="center", va="center", fontsize=6.2,
                    color=c["ink"], family="monospace", linespacing=1.15, zorder=5)
            if pruebas[k]:
                ax.add_patch(mpatches.Circle((x + ancho / 2, y - alto / 2), 0.13,
                                             facecolor=c["ground"], edgecolor=c["accent"],
                                             linewidth=1.1, zorder=6))
                ax.text(x + ancho / 2, y - alto / 2, str(pruebas[k]), ha="center",
                        va="center", fontsize=6, color=c["accent"], zorder=7)
            if nodo[k].partitions_def is not None:
                ax.text(x, y + alto / 2 + 0.11, f"{dias} días", ha="center", va="center",
                        fontsize=6, color=c["ink_faint"], zorder=5)
            if k in reintentos:
                ax.text(x, y + alto / 2 + 0.11, f"{reintentos[k]} reintentos", ha="center",
                        va="center", fontsize=6, color=c["ink_faint"], zorder=5)

        for x in sorted(columnas):
            ax.text(x * paso_x, -0.62, f"paso {x}", ha="center", va="center",
                    fontsize=7, color=c["ink_faint"])

        # Lo que significa cada marca, para que la figura se entienda sin la lección.
        abajo = (alto_max - 1) * paso_y + 0.62
        ax.text(-0.58, abajo, "el número en círculo: las comprobaciones que Dagster corre al "
                "terminar ese activo      el borde discontinuo: existe, pero aquí no se construye",
                ha="left", va="center", fontsize=6.6, color=c["ink_faint"])

        ax.set_xlim(-0.78, max(columnas) * paso_x + 0.78)
        ax.set_ylim(abajo + 0.3, -0.9)
        ax.set_xticks([])
        ax.set_yticks([])
        for lado in ax.spines:
            ax.spines[lado].set_visible(False)

    figura("fig_m29_grafo_de_activos", dibujar, ancho=9.4, alto=5.1, module=29)
    guardar_huellas(["fig_m29_grafo_de_activos"])
    print(f"  {len(claves)} activos, {len(aristas)} flechas y {sum(pruebas.values())} "
          f"comprobaciones, leídos de las definiciones de Dagster")


if __name__ == "__main__":
    main()
