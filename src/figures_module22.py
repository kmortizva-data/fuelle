"""La figura del módulo 22: lo que pesa la copia y lo que tarda restaurarla.

A la izquierda los tres tamaños del mismo dato, que es donde está la sorpresa:
la copia comprimida cabe en menos que el Parquet del que salió, y en una docena
de veces menos que la tabla dentro del servidor.

A la derecha los dos tiempos, y el que importa es el segundo. Copiar lo hace
todo el mundo; restaurar es lo que casi nadie prueba, y es lo único que
convierte un fichero de copia en una copia de seguridad.

Correr:  .venv\Scripts\python.exe src\figures_module22.py
"""

from __future__ import annotations

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
DATOS = PROJECT / "results" / "m22_copias.json"
DEL_19 = PROJECT / "results" / "m19_postgres.json"


def main() -> None:
    for f in (DATOS, DEL_19):
        if not f.exists():
            raise SystemExit(f"Falta {f.name}. Corre src/db/backup.py y src/db/load_silver.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    m19 = json.loads(io.open(DEL_19, encoding="utf-8").read())

    tamanos = [("en el servidor", m19["mb_en_el_servidor"]),
               ("en Parquet", m19["mb_en_parquet"]),
               ("la copia", d["mb_de_la_copia"])]
    tiempos = [("copiar", d["segundos_en_copiar"]),
               ("restaurar", d["segundos_en_restaurar"])]

    name = "fig_m22_copia_y_restauracion"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=22)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 2.9),
                                           gridspec_kw={"wspace": 0.34})

            colores = [c["ink_faint"], c["ink_faint"], c["accent"]]
            izq.barh(range(3), [v for _, v in tamanos], height=0.55,
                     color=colores, zorder=3)
            for i, (_, v) in enumerate(tamanos):
                izq.text(v + max(v for _, v in tamanos) * 0.02, i, f"{es(v, 1)} MB",
                         va="center", fontsize=8, color=c["ink_soft"])
            izq.set_yticks(range(3))
            izq.set_yticklabels([n for n, _ in tamanos], fontsize=9)
            izq.set_xlim(0, max(v for _, v in tamanos) * 1.3)
            izq.set_xlabel("MB del mismo dato")

            der.barh(range(2), [v for _, v in tiempos], height=0.5,
                     color=[c["ink_faint"], c["accent"]], zorder=3)
            for i, (_, v) in enumerate(tiempos):
                der.text(v + max(v for _, v in tiempos) * 0.02, i, f"{es(v, 1)} s",
                         va="center", fontsize=8, color=c["ink_soft"])
            der.set_yticks(range(2))
            der.set_yticklabels([n for n, _ in tiempos], fontsize=9)
            der.set_xlim(0, max(v for _, v in tiempos) * 1.32)
            der.set_xlabel("segundos")

            for ax in (izq, der):
                ax.invert_yaxis()
                ax.tick_params(length=0)
                ax.spines["left"].set_visible(False)
                ax.grid(axis="x", zorder=0)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])


if __name__ == "__main__":
    main()
