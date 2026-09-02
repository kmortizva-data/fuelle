"""La figura del módulo 20: qué guarda protege qué columna.

Misma rejilla que la del módulo 16, y no por comodidad: es literalmente el mismo
contrato, con la diferencia de quién lo hace cumplir. Allí las promesas las
comprobaba un script después de escribir; aquí las impone el motor y la
escritura no llega a entrar.

Ninguna casilla está escrita a mano. Sale de `pg_constraint` y de
`information_schema`, o sea de lo que la propia base dice de sí misma, igual que
el linaje del módulo 17 sale del manifest de dbt.

Correr:  .venv\\Scripts\\python.exe src\\figures_module20.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, fingerprint,  # noqa: E402
                           guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m20_esquema.json"

TIPOS = ["clave primaria", "clave foránea", "no vacío", "condición"]


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m20_esquema.json. Corre src/db/schema.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    filas = d["por_columna"]
    etiquetas = [f"{r['tabla']}.{r['columna']}" for r in filas]

    name = "fig_m20_esquema"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=20)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.2, 4.2))

            for j, fila in enumerate(filas):
                for i, tipo in enumerate(TIPOS):
                    puesta = tipo in fila["guardas"]
                    ax.add_patch(plt.Rectangle(
                        (i - 0.42, j - 0.42), 0.84, 0.84,
                        facecolor=c["accent"] if puesta else c["rule"],
                        edgecolor="none", zorder=3))

            ax.set_xticks(range(len(TIPOS)))
            ax.set_xticklabels(TIPOS, fontsize=8.5)
            ax.set_yticks(range(len(etiquetas)))
            ax.set_yticklabels(etiquetas, fontsize=8.5, family="monospace")
            ax.set_xlim(-0.6, len(TIPOS) - 0.4)
            ax.set_ylim(-0.6, len(etiquetas) - 0.4)
            ax.invert_yaxis()
            ax.tick_params(length=0)
            for lado in ("left", "bottom"):
                ax.spines[lado].set_visible(False)
            ax.set_xlabel("la guarda que el motor impone, leída de su propio catálogo")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {len(filas)} columnas protegidas, {d['guardas']} guardas en total")


if __name__ == "__main__":
    main()
