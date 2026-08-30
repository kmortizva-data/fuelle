"""La figura del módulo 2: una señal analógica y una digital, la misma hora.

No hay forma más corta de explicar la diferencia que ponerlas una encima de otra
con el mismo eje de tiempo. Arriba una presión, que toma miles de valores y
dibuja una curva. Abajo una válvula, que solo sabe decir sí o no y dibuja
escalones.

Correr:  .venv\\Scripts\\python.exe src\\figures_module2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import FIGURES, _style, colours, fingerprint, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"


def main() -> None:
    con = duckdb.connect()
    filas = con.sql(f"""
        SELECT timestamp, TP3, COMP
        FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')
        WHERE timestamp >= TIMESTAMP '2020-02-10 08:00:00'
          AND timestamp <  TIMESTAMP '2020-02-10 09:00:00'
        ORDER BY timestamp
    """).fetchall()
    if not filas:
        raise SystemExit("No hay datos en esa ventana.")

    t = [r[0] for r in filas]
    presion = [r[1] for r in filas]
    valvula = [r[2] for r in filas]

    # Dos paneles compartiendo el eje del tiempo, así que no vale `figura()`,
    # que crea un solo eje. Se repite su bucle de temas a mano.
    FIGURES.mkdir(exist_ok=True)
    name = "fig_m2_analogica_vs_digital"
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=2)
        with plt.rc_context(_style(theme, c)):
            fig, (arriba, abajo) = plt.subplots(
                2, 1, figsize=(9.2, 3.6), sharex=True,
                gridspec_kw={"height_ratios": [2, 1], "hspace": 0.18},
            )

            arriba.plot(t, presion, color=c["accent"], linewidth=1.4)
            arriba.set_ylabel("TP3, bar")
            arriba.grid(axis="y")
            arriba.annotate("analógica: 3.683 valores distintos", xy=(0.015, 0.86),
                            xycoords="axes fraction", fontsize=8.5, color=c["ink_soft"])

            # `steps-post` y no una línea: una señal digital no pasa por los
            # valores intermedios, salta. Dibujarla con línea recta sería
            # inventarse una rampa que la válvula nunca hizo.
            abajo.step(t, valvula, where="post", color=c["measured"], linewidth=1.4)
            abajo.set_ylabel("COMP")
            abajo.set_yticks([0, 1])
            abajo.set_ylim(-0.25, 1.25)
            abajo.grid(axis="y")
            abajo.annotate("digital: 2 valores, y nada en medio", xy=(0.015, 0.10),
                           xycoords="axes fraction", fontsize=8.5, color=c["ink_soft"])

            for eje in (arriba, abajo):
                for spine in ("left", "bottom"):
                    eje.spines[spine].set_linewidth(0.8)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  ventana: {t[0]} a {t[-1]} ({len(t)} lecturas)")
    print(f"  cambios de estado de COMP: "
          f"{sum(1 for i in range(1, len(valvula)) if valvula[i] != valvula[i-1])}")


if __name__ == "__main__":
    main()
