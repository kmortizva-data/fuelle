"""La figura del módulo 16: qué promesa caza qué rotura.

Una rejilla con las roturas abajo y las promesas a la izquierda. Cada marca dice
que esa promesa se entera de esa rotura.

Lo que la figura tiene que dejar claro es la fila de abajo: la promesa que
faltaba en la primera versión del contrato, y su columna solitaria, que es la
rotura que se escapaba entera.

Correr:  .venv\\Scripts\\python.exe src\\figures_module16.py
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
DATOS = PROJECT / "results" / "m16_contrato.json"

# La promesa que faltaba, para poder marcarla aparte en el dibujo.
LA_QUE_FALTABA = "no llegan columnas de mas"

CORTO = {
    "una columna llega con otro nombre": "columna\nrenombrada",
    "la presion llega en milibares": "otra\nunidad",
    "aparece una columna que nadie anuncio": "columna\nnueva",
    "la ingesta corrio dos veces": "ingesta\nrepetida",
    "un recuento de lecturas negativo": "valor\nimposible",
}


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m16_contrato.json. "
                         "Corre src/transform/contracts.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    promesas = d["promesas_del_contrato"]
    roturas = [r["rotura"] for r in d["detalle"]]
    caza = {(r["rotura"], p) for r in d["detalle"] for p in r["promesas_rotas"]}

    name = "fig_m16_contrato_roto"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=16)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.2, 4.0))

            for j, promesa in enumerate(promesas):
                for i, rotura in enumerate(roturas):
                    pilla = (rotura, promesa) in caza
                    ax.add_patch(plt.Rectangle(
                        (i - 0.42, j - 0.42), 0.84, 0.84,
                        facecolor=c["accent"] if pilla else c["rule"],
                        edgecolor="none", zorder=3))

            ax.set_xticks(range(len(roturas)))
            ax.set_xticklabels([CORTO.get(r, r) for r in roturas], fontsize=8.5)
            ax.set_yticks(range(len(promesas)))
            etiquetas = ax.set_yticklabels(promesas, fontsize=8.5)
            # La promesa que faltaba, en el acento, para que se la encuentre.
            for tick, promesa in zip(etiquetas, promesas):
                if promesa == LA_QUE_FALTABA:
                    tick.set_color(c["accent"])

            ax.set_xlim(-0.6, len(roturas) - 0.4)
            ax.set_ylim(-0.6, len(promesas) - 0.4)
            ax.invert_yaxis()
            ax.tick_params(length=0)
            for lado in ("left", "bottom"):
                ax.spines[lado].set_visible(False)
            ax.set_xlabel("la rotura que llega el lunes; encendido, la promesa que se entera")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {len(promesas)} promesas contra {len(roturas)} roturas, "
          f"{d['roturas_cazadas']} cazadas")


if __name__ == "__main__":
    main()
