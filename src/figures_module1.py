"""Las figuras del módulo 1: el encargo.

Una sola, y de datos reales: el ciclo de trabajo diario a lo largo de los siete
meses, con las cuatro averías documentadas marcadas encima. Es la figura que
plantea el proyecto entero sin decir una palabra.

El diagrama del compresor no se dibuja aquí: es un esquema conceptual y sale
mejor en SVG dentro de la propia página que en matplotlib.

Correr:  .venv\\Scripts\\python.exe src\\figures_module1.py
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DUTY = PROJECT / "results" / "m10_duty_cycle.json"

# Las cuatro averías, con las fechas literales del PDF oficial. Los rangos van
# como fechas de inicio y fin, tal y como los declara el parte.
AVERIAS = [
    (date(2020, 4, 18), date(2020, 4, 18), "#1"),
    (date(2020, 5, 29), date(2020, 5, 30), "#1"),
    (date(2020, 6, 5), date(2020, 6, 7), "#3"),
    (date(2020, 7, 15), date(2020, 7, 15), "#4"),
]

FULL_DAY = 8640


def main() -> None:
    if not DUTY.exists():
        raise SystemExit("Falta results/m10_duty_cycle.json. Corre src/transform/m10_duty_cycle.py")

    datos = json.loads(io.open(DUTY, encoding="utf-8").read())
    completos = [d for d in datos["daily"] if d["readings"] > 0.9 * FULL_DAY]
    parciales = [d for d in datos["daily"] if d["readings"] <= 0.9 * FULL_DAY]

    x_ok = [date.fromisoformat(d["day"]) for d in completos]
    y_ok = [d["loaded_hours"] for d in completos]
    x_no = [date.fromisoformat(d["day"]) for d in parciales]
    y_no = [d["loaded_hours"] for d in parciales]
    media = datos["avg_loaded_hours"]

    dias_averia = set()
    for inicio, fin, _ in AVERIAS:
        d = inicio
        while d <= fin:
            dias_averia.add(d)
            d = date.fromordinal(d.toordinal() + 1)
    x_av = [d for d in x_ok if d in dias_averia]
    y_av = [y for d, y in zip(x_ok, y_ok) if d in dias_averia]

    def dibujar(fig, ax, c):
        # Las bandas de avería, detrás de todo. Con un ancho mínimo de día y
        # medio a cada lado: las averías de un solo día (18 de abril, que es el
        # pico de 23,81 h, y 15 de julio) salían como líneas de un píxel y no se
        # veían, que era justo perder lo que la figura tiene que enseñar.
        for inicio, fin, etiqueta in AVERIAS:
            izq = date.fromordinal(inicio.toordinal() - 2)
            der = date.fromordinal(fin.toordinal() + 2)
            ax.axvspan(izq, der, color=c["simulated"], alpha=0.20, linewidth=0, zorder=1)
            ax.annotate(etiqueta, xy=(izq, 24.6), fontsize=7.5, color=c["simulated"],
                        ha="center", va="top", zorder=6)

        ax.axhline(media, color=c["ink_faint"], linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
        ax.annotate(f"media {media} h", xy=(x_ok[2], media + 0.5), fontsize=8,
                    color=c["ink_faint"], zorder=5)

        # Los días incompletos van apagados: están, pero no cuentan para la media.
        ax.scatter(x_no, y_no, s=9, color=c["ink_faint"], alpha=0.4, zorder=3,
                   label="día incompleto")
        ax.scatter(x_ok, y_ok, s=14, color=c["accent"], zorder=4, label="día completo")
        # Un anillo sobre los días con parte de avería: la banda sola depende del
        # color, y el anillo funciona también en blanco y negro.
        ax.scatter(x_av, y_av, s=62, facecolors="none", edgecolors=c["simulated"],
                   linewidths=1.3, zorder=5, label="día con parte de avería")

        ax.set_ylabel("horas en carga")
        ax.set_ylim(0, 25)
        ax.set_yticks([0, 6, 12, 18, 24])
        ax.grid(axis="y", zorder=0)
        ax.legend(frameon=False, fontsize=8, loc="upper left",
                  bbox_to_anchor=(0, 1.04), ncol=3, labelcolor=c["ink_soft"])
        for spine in ("left", "bottom"):
            ax.spines[spine].set_linewidth(0.8)

    figura("fig_m1_las_cuatro_averias", dibujar, ancho=9.2, alto=3.6, module=1)
    guardar_huellas(["fig_m1_las_cuatro_averias"])
    print()
    print(f"  días completos   {len(completos)}")
    print(f"  días parciales   {len(parciales)}")
    print(f"  media            {media} h")




def anatomia() -> None:
    """La anatomía del compresor contada con sus propias señales.

    Un diagrama dibujado a mano diría lo mismo peor: aquí se ve el ciclo de
    carga y vacío de verdad, con la presión subiendo mientras el motor consume
    y bajando cuando para. Dos horas de un día tranquilo.
    """
    import duckdb

    con = duckdb.connect()
    bronze = (PROJECT / "lake" / "bronze" / "telemetry").as_posix()
    filas = con.sql(f"""
        SELECT timestamp, TP3, Motor_current, DV_eletric
        FROM read_parquet('{bronze}/**/*.parquet')
        WHERE timestamp >= TIMESTAMP '2020-02-10 08:00:00'
          AND timestamp <  TIMESTAMP '2020-02-10 10:00:00'
        ORDER BY timestamp
    """).fetchall()
    if not filas:
        raise SystemExit("No hay datos en esa ventana; elige otra.")

    t = [r[0] for r in filas]
    presion = [r[1] for r in filas]
    corriente = [r[2] for r in filas]
    carga = [r[3] for r in filas]

    def dibujar(fig, ax, c):
        # Las franjas de carga, detrás: son el ciclo que hay que ver.
        inicio = None
        for i, v in enumerate(carga):
            if v == 1 and inicio is None:
                inicio = t[i]
            elif v == 0 and inicio is not None:
                ax.axvspan(inicio, t[i], color=c["accent"], alpha=0.13, linewidth=0, zorder=1)
                inicio = None
        if inicio is not None:
            ax.axvspan(inicio, t[-1], color=c["accent"], alpha=0.13, linewidth=0, zorder=1)

        ax.plot(t, presion, color=c["measured"], linewidth=1.4, zorder=3)
        ax.axhline(8.2, color=c["simulated"], linewidth=1, linestyle=(0, (4, 3)), zorder=2)
        ax.annotate("8,2 bar: el umbral de arranque", xy=(t[300], 8.30), fontsize=8,
                    color=c["simulated"], zorder=5, ha="left")
        ax.set_ylabel("presión del panel, bar")
        ax.set_ylim(7.8, 10.2)

        derecha = ax.twinx()
        derecha.plot(t, corriente, color=c["ink_faint"], linewidth=0.9, alpha=0.85, zorder=2)
        derecha.set_ylabel("corriente del motor, A")
        derecha.set_ylim(-1, 12)
        derecha.spines["top"].set_visible(False)
        derecha.tick_params(colors=c["ink_faint"])
        derecha.yaxis.label.set_color(c["ink_soft"])
        derecha.spines["right"].set_color(c["rule"])
        derecha.spines["right"].set_visible(True)

        ax.grid(axis="y", zorder=0)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_linewidth(0.8)

    figura("fig_m1_anatomia_del_compresor", dibujar, ancho=9.2, alto=3.2, module=1)
    guardar_huellas(["fig_m1_anatomia_del_compresor"])
    print(f"  ventana: {t[0]} a {t[-1]}  ({len(t)} lecturas)")
    print(f"  presión: {min(presion):.2f} a {max(presion):.2f} bar")
    print(f"  ciclos de carga en la ventana: "
          f"{sum(1 for i, v in enumerate(carga) if v == 1 and (i == 0 or carga[i-1] == 0))}")


if __name__ == "__main__":
    main()
    print()
    anatomia()
