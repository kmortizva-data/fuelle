"""La figura del módulo 5: la misma ingesta, tres veces, con huella y sin ella.

Dos líneas y una de ellas sube. Eso es todo lo que hay que entender del módulo,
y en un dibujo se ve antes que en un párrafo.

La línea de la verdad va discontinua porque es la referencia, no una medida: son
las filas que hay en el origen y que deberían estar en el destino corra lo que
corra.

Correr:  .venv\\Scripts\\python.exe src\\figures_module5.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m05_fingerprint.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m05_fingerprint.json. "
                         "Corre src/ingest/fingerprint.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    corridas = list(range(1, d["corridas_del_experimento"] + 1))
    naive = [n / 1e6 for n in d["filas_naive_por_corrida"]]
    guarded = [n / 1e6 for n in d["filas_guarded_por_corrida"]]
    verdad = d["filas_origen"] / 1e6

    def dibujar(fig, ax, c):
        ax.axhline(verdad, color=c["ink_faint"], linestyle="--", linewidth=1.1, zorder=2)
        ax.annotate("lo que hay en el origen", xy=(corridas[0], verdad),
                    xytext=(0, -14), textcoords="offset points",
                    fontsize=8, color=c["ink_faint"])

        ax.plot(corridas, naive, marker="o", markersize=5, linewidth=1.8,
                color=c["accent"], zorder=4, label="sin huella: vuelve a ingerir siempre")
        ax.plot(corridas, guarded, marker="s", markersize=5, linewidth=1.8,
                color=c["ink_soft"], zorder=5, label="con huella: solo si el origen cambió")

        for x, y in zip(corridas, naive):
            ax.annotate(f"{y:.2f} M", xy=(x, y), xytext=(0, 8),
                        textcoords="offset points", ha="center",
                        fontsize=8, color=c["accent"])
        ax.annotate(f"{guarded[-1]:.2f} M", xy=(corridas[-1], guarded[-1]),
                    xytext=(0, -16), textcoords="offset points", ha="center",
                    fontsize=8, color=c["ink_soft"])

        ax.set_xlabel("veces que se corre la misma ingesta")
        ax.set_ylabel("millones de filas en el destino")
        ax.set_xticks(corridas)
        ax.set_ylim(0, max(naive) * 1.2)
        ax.grid(axis="y", zorder=0)
        ax.legend(loc="upper left", frameon=False, fontsize=8)

    figura("fig_m5_idempotencia", dibujar, ancho=8.4, alto=3.2, module=5)
    guardar_huellas(["fig_m5_idempotencia"])
    print(f"  sin huella acaba en {d['filas_naive_al_final']:,}, "
          f"con huella en {d['filas_guarded_al_final']:,}")


if __name__ == "__main__":
    main()
