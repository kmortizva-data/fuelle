"""The figure of module 27: the residual over seven months, read two ways.

Two panels, one above the other, on the same clock, because the module's result
is that **the same number answers two different questions** and you need both.

Above, the **frozen** residual: every hour against February. It has a floor,
which is how high a healthy hour ever got, and a ceiling, which is where it pins
when the compressor stops stopping. What it shows is a machine that leaves
February in March and never comes back.

Below, the **rolling** one: each day against the median of the fourteen before
it. The drift cancels, so what is left are the events. The four reports are
marked on both, and so are the twelve undocumented days of March.

Run:  .venv\\Scripts\\python.exe src\\figures_module27.py
"""

from __future__ import annotations

import datetime
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                           guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
DATOS = PROJECT / "results" / "m27_residual.json"
RESULTS = PROJECT / "results" / "m27_figura.json"


def dia_a_dia(entrega: float, consumo: float) -> list[dict]:
    """El indicador móvil, día a día, tal como lo define residual.py."""
    con = duckdb.connect()
    con.execute(f"CREATE VIEW p AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet') WHERE medido")
    filas = con.sql(f"""
        WITH h AS (
          SELECT date_trunc('hour', timestamp) AS hora, day,
                 avg(DV_eletric) * {entrega} - {consumo} AS residual
          FROM p GROUP BY 1, 2 HAVING count(*) >= 300
        ), d AS (SELECT day, max(residual) AS pico FROM h GROUP BY day)
        SELECT day, pico,
               pico - median(pico) OVER (ORDER BY day
                        ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS sobre
        FROM d ORDER BY day
    """).fetchall()
    con.close()
    return [{"dia": datetime.date.fromisoformat(str(f[0])), "pico": float(f[1]),
             "sobre": None if f[2] is None else float(f[2])} for f in filas]


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Faltan las cifras. Corre src/twin/residual.py primero.")
    d = json.load(io.open(DATOS, encoding="utf-8"))

    serie = [(datetime.datetime.fromisoformat(x["hora"]), x["residual"])
             for x in d["serie_horaria"]]
    diario = dia_a_dia(d["entrega"], d["consumo"])
    suelo, techo = d["suelo"]["maximo"], d["censura"]["techo"]
    marzo = [datetime.date.fromisoformat(x) for x in d["evento_de_marzo"]]
    partes = [datetime.datetime.fromisoformat(p["empieza"]) for p in d["partes"]]

    name = "fig_m27_residual"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        col = colours(theme, module=27)
        with plt.rc_context(_style(theme, col)):
            fig, (arriba, abajo) = plt.subplots(
                2, 1, figsize=(9.2, 5.0), sharex=True,
                gridspec_kw={"hspace": 0.16, "height_ratios": [1.35, 1]})

            # Los doce días de marzo, en los dos paneles, para que se vea que el
            # gemelo los marca igual que a los que sí tienen parte.
            for ax in (arriba, abajo):
                ax.axvspan(marzo[0], marzo[1], color=col["accent"], alpha=0.16,
                           zorder=1)
                for t in partes:
                    ax.axvline(t, color=col["simulated"], linewidth=1.1,
                               linestyle="--", zorder=2)

            arriba.axhspan(0, suelo, color=col["measured"], alpha=0.12, zorder=1)
            arriba.axhline(techo, color=col["ink_faint"], linewidth=1.0,
                           linestyle=":", zorder=3)
            arriba.plot([t for t, _ in serie], [v for _, v in serie],
                        color=col["measured"], linewidth=0.5, zorder=4)
            # Las dos etiquetas van a la derecha: pegadas al origen chocaban con
            # el rótulo del eje y la del suelo quedaba encima de la curva.
            arriba.annotate("el techo: el compresor no para",
                            xy=(serie[-1][0], techo), fontsize=8,
                            color=col["ink_soft"], ha="right", va="bottom",
                            xytext=(-4, 4), textcoords="offset points")
            # La del suelo va sobre febrero, que es donde la banda está vacía:
            # al borde derecho caía encima de la curva.
            arriba.annotate("el suelo de febrero",
                            xy=(serie[len(serie) // 8][0], suelo), fontsize=8,
                            color=col["ink_soft"], ha="center", va="bottom",
                            xytext=(0, 6), textcoords="offset points")
            # Y qué es cada marca, dicho una vez y no en la prosa.
            arriba.plot([], [], color=col["simulated"], linewidth=1.1,
                        linestyle="--", label="los cuatro partes de avería")
            arriba.fill_between([], [], color=col["accent"], alpha=0.16,
                                label="marzo, doce días sin parte")
            arriba.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
            arriba.set_ylabel("residual congelado, bar/min")
            arriba.set_ylim(-0.05, techo * 1.18)

            con_base = [x for x in diario if x["sobre"] is not None]
            abajo.axhline(0, color=col["ink_faint"], linewidth=0.9, zorder=2)
            abajo.plot([x["dia"] for x in con_base],
                       [x["sobre"] for x in con_base],
                       color=col["measured"], linewidth=1.1, zorder=4)
            abajo.set_ylabel("sobre los 14 días previos")
            abajo.set_xlabel("de febrero a agosto de 2020")

            for ax in (arriba, abajo):
                ax.grid(axis="y", zorder=0)
            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    guardar_huellas([name])

    # Lo que la figura enseña, en números, para que la prosa no lo estime a ojo.
    picos = {p["empieza"][:10]: p for p in d["partes"]}
    payload = {
        "horas_dibujadas": len(serie),
        "dias_con_referencia": len(con_base),
        "suelo": suelo, "techo": techo,
        # El indicador móvil en los días de parte, que es lo que lo justifica.
        "sobre_la_tendencia_en_los_partes": [
            {"dia": x["dia"].isoformat(), "sobre": round(x["sobre"], 4)}
            for x in con_base if x["dia"].isoformat() in picos],
        "sobre_la_tendencia_mediana": round(
            sorted(x["sobre"] for x in con_base)[len(con_base) // 2], 4),
        "sobre_la_tendencia_p95": round(
            sorted(x["sobre"] for x in con_base)[int(len(con_base) * 0.95)], 4),
    }
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"  {len(serie)} horas dibujadas, {len(con_base)} días con referencia")
    print(f"  el móvil, en día corriente: mediana "
          f"{es(payload['sobre_la_tendencia_mediana'], 4)}, p95 "
          f"{es(payload['sobre_la_tendencia_p95'], 4)}")
    for x in payload["sobre_la_tendencia_en_los_partes"]:
        print(f"    {x['dia']}   sobre la tendencia {x['sobre']}")


if __name__ == "__main__":
    main()
