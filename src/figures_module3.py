"""La figura del módulo 3: los cuatro sitios, en tamaño y en tiempo.

El tiempo lleva su rango dibujado encima. Sin él, la barra de la base de
datos y la del almacén parecerían dos medidas distintas, y lo que dicen los
rangos es que se solapan: no hay diferencia que enseñar.

Dos barras horizontales por sitio no funcionarían, porque los tiempos van de
seis décimas a tres milésimas y la barra pequeña desaparecería. Se usa escala
logarítmica en el tiempo y se dice en el pie, que es la única forma honesta de
enseñar cuatro números que se separan doscientas veces.

Correr:  .venv\\Scripts\\python.exe src\\figures_module3.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import FIGURES, _style, colours, fingerprint, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m03_donde_viven.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m03_donde_viven.json. Corre src/ingest/donde_viven.py")

    datos = json.loads(io.open(DATOS, encoding="utf-8").read())
    sitios = datos["sitios"]
    nombres = [s["sitio"] for s in sitios]
    tamaños = [s["mb"] for s in sitios]
    tiempos = [s["mediana_s"] for s in sitios]
    bajos = [s["mediana_s"] - s["min_s"] for s in sitios]
    altos = [s["max_s"] - s["mediana_s"] for s in sitios]
    y = range(len(sitios))

    name = "fig_m3_cuatro_sitios"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=3)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 2.9), sharey=True,
                                           gridspec_kw={"wspace": 0.08})

            izq.barh(list(y), tamaños, height=0.55, color=c["ink_faint"], zorder=3)
            izq.set_xlabel("tamaño en disco, MB")
            izq.invert_yaxis()
            izq.set_yticks(list(y))
            izq.set_yticklabels(nombres)
            izq.grid(axis="x", zorder=0)
            for i, v in zip(y, tamaños):
                izq.annotate(f"{v:,.0f}", xy=(v, i), xytext=(5, 0),
                             textcoords="offset points", va="center",
                             fontsize=8, color=c["ink_soft"])
            izq.set_xlim(0, max(tamaños) * 1.22)

            der.barh(list(y), tiempos, height=0.55, color=c["accent"], zorder=3,
                     xerr=[bajos, altos], error_kw={"ecolor": c["ink_faint"],
                                                    "elinewidth": 1, "capsize": 3})
            der.set_xscale("log")
            der.set_xlabel("segundos, mediana de 7 corridas y su rango (escala logarítmica)")
            der.grid(axis="x", zorder=0)
            for i, v in zip(y, tiempos):
                der.annotate(f"{v:.3f}", xy=(v, i), xytext=(5, 0),
                             textcoords="offset points", va="center",
                             fontsize=8, color=c["ink_soft"])
            der.set_xlim(min(tiempos) * 0.45, max(tiempos) * 3.2)

            for eje in (izq, der):
                for spine in ("left", "bottom"):
                    eje.spines[spine].set_linewidth(0.8)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {datos['veces_entre_extremos']} veces entre el más lento y el más rápido")


if __name__ == "__main__":
    main()
