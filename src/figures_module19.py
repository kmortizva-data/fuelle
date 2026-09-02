"""La figura del módulo 19: qué cambia de verdad al pasar de fichero a servicio.

Dos paneles, y el orden es el del hallazgo. A la izquierda, la misma pregunta
hecha a los dos: las barras se pisan, así que **responder no cuesta más**. A la
derecha, lo que ocupa la misma tabla en cada sitio, que es donde sí hay
diferencia y es de once veces.

Se dibuja así a propósito. La expectativa era que un motor columnar ganara de
calle a uno de filas en una pregunta analítica, y a esta escala no pasa. Lo que
un servicio cobra es el disco y la carga, no la respuesta, y la figura tiene que
enseñar eso y no lo que yo esperaba.

Correr:  .venv\\Scripts\\python.exe src\\figures_module19.py
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
DATOS = PROJECT / "results" / "m19_postgres.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m19_postgres.json. Corre src/db/load_silver.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    p = d["pregunta"]

    name = "fig_m19_fichero_vs_servicio"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=19)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 3.0),
                                           gridspec_kw={"wspace": 0.32})

            # --- Responder: se pisan --------------------------------------
            etiquetas = ["un fichero", "un servicio"]
            colores = [c["ink_faint"], c["accent"]]
            for i, (clave, color) in enumerate(zip(("fichero", "servicio"), colores)):
                m = p[clave]
                izq.barh(i, m["mediana"], height=0.5, color=color, zorder=3)
                izq.plot([m["minimo"], m["maximo"]], [i, i], color=c["ink"],
                         linewidth=1.1, zorder=4)
                izq.text(m["maximo"] + 0.02, i, f"{es(m['mediana'], 3)} s",
                         va="center", fontsize=8, color=c["ink_soft"])
            izq.set_yticks(range(2))
            izq.set_yticklabels(etiquetas, fontsize=9)
            izq.invert_yaxis()
            izq.set_xlim(0, max(p[k]["maximo"] for k in ("fichero", "servicio")) * 1.5)
            izq.set_xlabel("segundos en responder la misma pregunta")
            izq.set_title("los rangos se pisan: no se distinguen", fontsize=9,
                          color=c["ink_soft"], pad=8)

            # --- Guardar: once veces --------------------------------------
            mb = [d["mb_en_parquet"], d["mb_en_el_servidor"]]
            der.barh(range(2), mb, height=0.5, color=colores, zorder=3)
            for i, v in enumerate(mb):
                der.text(v + max(mb) * 0.02, i, f"{es(v, 1)} MB", va="center",
                         fontsize=8, color=c["ink_soft"])
            der.set_yticks(range(2))
            der.set_yticklabels(etiquetas, fontsize=9)
            der.invert_yaxis()
            der.set_xlim(0, max(mb) * 1.35)
            der.set_xlabel("MB que ocupan las mismas lecturas")
            der.set_title(f"{es(d['veces_mas_disco_el_servidor'], 1)} veces más disco",
                          fontsize=9, color=c["ink_soft"], pad=8)

            for ax in (izq, der):
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
