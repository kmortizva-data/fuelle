"""La figura del módulo 17: el mapa del lago, dibujado por el propio dbt.

Ni un nodo ni una flecha están escritos aquí. Todo sale de
`dbt/target/manifest.json`, que dbt escribe cada vez que compila el proyecto, y
que a su vez sale de los `ref()` y `source()` que hay dentro del SQL.

Ese es el argumento entero del módulo, así que dibujar el grafo a mano lo
destruiría: si el mapa se hace solo, hay que enseñarlo haciéndose solo. Si mañana
alguien añade un modelo, esta figura lo tendrá sin tocar una línea.

La columna de cada nodo es su capa, que es la carpeta donde vive el fichero. La
altura dentro de la columna sí se calcula: es la profundidad en el grafo, o sea
cuántos saltos hay desde la fuente más lejana, que es el mismo cálculo con el que
dbt decide qué construir antes. Por eso `oro_averias`, que se apoya en otra tabla
de oro, cae por debajo de ella y recibe una flecha vertical.

Correr:  .venv\\Scripts\\python.exe src\\figures_module17.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "transform"))

from dbt_gold import MANIFEST, linaje  # noqa: E402
from figures_theme import figura, guardar_huellas  # noqa: E402

CAPAS = {"fuente": "el lago", "preparacion": "preparación", "oro": "oro"}


def profundidades(nodos: dict, aristas: list) -> dict[str, int]:
    """Cuántos saltos hay desde la fuente más lejana hasta cada nodo.

    Es el orden en que dbt construye, y aquí decide la altura dentro de cada
    columna: un modelo queda por debajo de aquellos de los que depende. Ese
    escalón no lo he decidido yo, está en el SQL.
    """
    padres: dict[str, list[str]] = {u: [] for u in nodos}
    for a, b in aristas:
        padres[b].append(a)

    nivel: dict[str, int] = {}

    def calcula(u: str) -> int:
        if u not in nivel:
            nivel[u] = 0 if not padres[u] else 1 + max(calcula(p) for p in padres[u])
        return nivel[u]

    for u in nodos:
        calcula(u)
    return nivel


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit("Falta dbt/target/manifest.json. "
                         "Corre src/transform/dbt_gold.py")

    g = linaje()
    nodos, aristas = g["nodos"], g["aristas"]
    nivel = profundidades(nodos, aristas)

    # Una columna por capa, y dentro de ella los nodos por profundidad. El
    # desempate por nombre existe para que la figura no cambie de un día para
    # otro sin que haya cambiado el proyecto.
    columnas: dict[int, list[str]] = {}
    orden = {"fuente": 0, "preparacion": 1, "oro": 2}
    for u in sorted(nodos, key=lambda u: (nivel[u], nodos[u]["nombre"])):
        columnas.setdefault(orden[nodos[u]["capa"]], []).append(u)

    sitio = {}
    alto_max = max(len(c) for c in columnas.values())
    for x, us in columnas.items():
        hueco = (alto_max - len(us)) / 2
        for y, u in enumerate(us):
            sitio[u] = (x, hueco + y)

    def dibujar(fig, ax, c) -> None:
        tono = {"fuente": c["ink_faint"], "preparacion": c["ink_soft"],
                "oro": c["accent"]}
        ancho, alto = 0.78, 0.42

        for a, b in aristas:
            xa, ya = sitio[a]
            xb, yb = sitio[b]
            if xa == xb:
                # Dentro de la misma columna, el caso de una tabla de oro que se
                # apoya en otra. Va rodeando por fuera y no en linea recta: una
                # recta atravesaria la caja de en medio y parecerian dos saltos.
                desde, hasta = (xa + ancho / 2, ya), (xb + ancho / 2, yb)
                curva = "arc3,rad=-0.8"
            else:
                desde, hasta = (xa + ancho / 2, ya), (xb - ancho / 2, yb)
                curva = "arc3,rad=0.08"
            ax.annotate(
                "", xy=hasta, xytext=desde,
                arrowprops=dict(arrowstyle="-|>", color=c["rule"],
                                linewidth=1.1, shrinkA=3, shrinkB=3,
                                connectionstyle=curva),
                zorder=2)

        for u, (x, y) in sitio.items():
            capa = nodos[u]["capa"]
            ax.add_patch(plt_rect(x - ancho / 2, y - alto / 2, ancho, alto,
                                  c["panel"], tono[capa]))
            ax.text(x, y, nodos[u]["nombre"], ha="center", va="center",
                    fontsize=7.6, color=c["ink"], family="monospace", zorder=5)

        # La etiqueta de cada columna, con la capa a la que pertenece.
        for x, us in sorted(columnas.items()):
            capa = CAPAS[nodos[us[0]]["capa"]]
            ax.text(x, -0.85, capa, ha="center", va="center", fontsize=8,
                    color=c["ink_faint"])

        ax.set_xlim(-0.74, max(columnas) + 0.74)
        ax.set_ylim(alto_max - 0.45, -1.15)
        ax.set_xticks([])
        ax.set_yticks([])
        for lado in ax.spines:
            ax.spines[lado].set_visible(False)

    figura("fig_m17_linaje_dbt", dibujar, ancho=9.2, alto=3.2, module=17)
    guardar_huellas(["fig_m17_linaje_dbt"])
    print(f"  {len(nodos)} nodos y {len(aristas)} flechas, "
          f"leídos del manifest de dbt")


def plt_rect(x, y, w, h, cara, borde):
    import matplotlib.patches as mpatches
    return mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
        facecolor=cara, edgecolor=borde, linewidth=1.3, zorder=4)


if __name__ == "__main__":
    main()
