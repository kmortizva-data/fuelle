"""La figura del módulo 23: el gemelo al lado de la máquina, y lo que los separa.

Dos días, y el mismo gemelo en los dos. A la izquierda un día sano, donde las dos
curvas van juntas. A la derecha el 18 de abril, la primera avería documentada,
donde se abren y el hueco entre ellas se pinta.

**Ese hueco es el residual**, y es todo lo que un gemelo tiene que dar. Aquí solo
se enseña; medirlo y decidir a partir de cuánto avisa es el módulo 27.

Las dos curvas son **minutos cargando acumulados**, nunca la presión. Es la regla
del curso, y viene de haberla medido: dibujar la presión no separa nada porque es
la variable que el control sostiene.

Correr:  .venv\\Scripts\\python.exe src\\figures_module23.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                           guardar_huellas)
from twin.model import mide  # noqa: E402
from twin.simulate import avanza  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m23_gemelo.json"

# Un día sano y **completo**, con sus 8.640 lecturas. Ha cambiado dos veces y las
# dos por el mismo motivo, que es no mirar lo que se elige. Primero fue el 2 de
# marzo, al que le faltan tres horas, y comparar un día incompleto contra una
# simulación de 24 h le regalaba minutos al gemelo. Después el 8 de marzo, que sí
# está completo pero **cae dentro de la avería no documentada de marzo** y era el
# día más cargado de todos los candidatos: 140 min contra los 81 de la mediana.
# Este es de febrero y es el más cercano a la mediana de los días completos.
SANO = "2020-02-18"
AVERIA = "2020-04-18"
PASO = 5 / 60           # el que salió del módulo 25
VENTANA = ("2020-02-01", "2020-02-29")   # la misma que calibra model.py


# El registro va a una lectura cada diez segundos y el gemelo corre a `PASO`, que
# desde el módulo 25 es más fino. Si se le dan tantos pasos como lecturas, el
# gemelo vive **la mitad del reloj** y se queda corto sin que sea culpa suya.
SEGUNDOS_POR_LECTURA = 10


def traza_del_gemelo(dep, lecturas: int, paso: float) -> list[float]:
    """Los minutos cargando del gemelo, en el mismo reloj que las lecturas."""
    minutos = lecturas * SEGUNDOS_POR_LECTURA / 60
    trabajo = avanza(dep, dep.consumo, minutos, paso)["trabajo"]
    cada = SEGUNDOS_POR_LECTURA / 60 / paso
    return [trabajo[min(int(round(i * cada)), len(trabajo) - 1)]
            for i in range(lecturas)]


def real(dia: str) -> list[float]:
    """Los minutos cargando acumulados de la máquina de verdad, ese día."""
    con = duckdb.connect()
    filas = con.sql(f"""
        SELECT sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                   OVER (ORDER BY timestamp) / 6.0 AS acumulado
        FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
        WHERE medido AND day = DATE '{dia}'
        ORDER BY timestamp
    """).fetchall()
    con.close()
    return [float(f[0]) for f in filas]


def dias_sanos_completos() -> list[tuple[str, float]]:
    """Todos los días enteros de la ventana sana, con lo que cargó cada uno.

    Hace falta para el suelo de ruido, y **un día suelto no sirve para eso**. La
    primera versión medía el error del gemelo contra un único día sano y lo
    dividía en el hueco de la avería. Con el día pegado a la mediana el hueco
    sale de 0,2 minutos y el cociente se dispara a más de seis mil, que no es un
    resultado: es dividir por casi cero. Lo que hay que enseñar es cuánto se
    mueven los días sanos entre ellos, porque eso es lo que un aviso tiene que
    superar para no sonar cada semana.
    """
    con = duckdb.connect()
    filas = con.sql(f"""
        SELECT day, sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) / 6.0 AS minutos
        FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
        WHERE medido AND day BETWEEN DATE '{VENTANA[0]}' AND DATE '{VENTANA[1]}'
        GROUP BY day HAVING count(*) = 8640
        ORDER BY day
    """).fetchall()
    con.close()
    return [(str(f[0]), float(f[1])) for f in filas]


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    dep, _ = mide()
    dias = []
    for dia, titulo in ((SANO, "un día sano"), (AVERIA, "el 18 de abril, la avería #1")):
        medido = real(dia)
        # El gemelo corre con el consumo de la ventana sana, SIEMPRE. No sabe que
        # hay una fuga, y por eso el día de avería se queda corto: esa distancia
        # es la que el módulo 27 va a convertir en un aviso.
        simulado = traza_del_gemelo(dep, len(medido), PASO)
        dias.append({"dia": dia, "titulo": titulo,
                     "medido": medido, "simulado": simulado})

    def dibujar(fig, ax, c) -> None:
        pass  # esta figura lleva dos paneles, así que se dibuja a mano

    name = "fig_m23_gemelo_y_residual"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        col = colours(theme, module=23)
        with plt.rc_context(_style(theme, col)):
            fig, ejes = plt.subplots(1, 2, figsize=(9.2, 3.2), sharey=True,
                                     gridspec_kw={"wspace": 0.08})
            for ax, d in zip(ejes, dias):
                horas = [i * SEGUNDOS_POR_LECTURA / 3600
                         for i in range(len(d["medido"]))]
                ax.fill_between(horas, d["simulado"], d["medido"],
                                color=col["accent"], alpha=0.16, zorder=2)
                ax.plot(horas, d["medido"], color=col["measured"], linewidth=1.8,
                        zorder=4, label="la máquina")
                ax.plot(horas, d["simulado"], color=col["simulated"], linewidth=1.8,
                        linestyle="--", zorder=4, label="el gemelo")
                ax.set_title(d["titulo"], fontsize=9, color=col["ink_soft"], pad=8)
                ax.set_xlabel("horas del día")
                ax.set_xlim(0, 24)
                ax.grid(axis="y", zorder=0)
            ejes[0].set_ylabel("minutos cargando, acumulados")
            ejes[0].legend(frameon=False, fontsize=8.5, loc="upper left")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])

    # El listón: cuánto se separan al final del día en cada caso. Es lo que el
    # residual tiene que saber distinguir, y lo que el módulo 28 tendrá que batir.
    payload = {"paso_s": round(PASO * 60, 1)}
    for d in dias:
        hueco = d["medido"][-1] - d["simulado"][-1]
        payload[d["dia"]] = {
            "minutos_reales": round(d["medido"][-1], 1),
            "minutos_del_gemelo": round(d["simulado"][-1], 1),
            "hueco_minutos": round(hueco, 1),
        }
    sano, averia = payload[SANO], payload[AVERIA]

    # El suelo de ruido, que sale del reparto de los días sanos y no de uno solo.
    # El gemelo predice lo mismo todos los días, así que el hueco de cada día es
    # lo que ese día se salió de la costumbre.
    prediccion = sano["minutos_del_gemelo"]
    completos = [{"dia": d, "minutos": round(m, 1),
                  "hueco_minutos": round(m - prediccion, 1)}
                 for d, m in dias_sanos_completos()]
    peor = max(abs(d["hueco_minutos"]) for d in completos)
    payload["dias_sanos_completos"] = completos
    payload["cuantos_dias_sanos"] = len(completos)
    payload["hueco_sano_mayor"] = round(peor, 1)
    payload["minutos_sanos_min"] = round(min(d["minutos"] for d in completos), 1)
    payload["minutos_sanos_max"] = round(max(d["minutos"] for d in completos), 1)
    # El listón de verdad: la avería contra el PEOR día sano, no contra el mejor.
    payload["veces_mas_hueco_en_la_averia"] = round(
        abs(averia["hueco_minutos"]) / peor, 1)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  día sano   : la máquina {sano['minutos_reales']} min, "
          f"el gemelo {sano['minutos_del_gemelo']}, hueco {sano['hueco_minutos']}")
    print(f"  los {len(completos)} días sanos completos van de "
          f"{payload['minutos_sanos_min']} a {payload['minutos_sanos_max']} min, "
          f"y el hueco mayor entre ellos es {payload['hueco_sano_mayor']}")
    print(f"  18 de abril: la máquina {averia['minutos_reales']} min, "
          f"el gemelo {averia['minutos_del_gemelo']}, hueco {averia['hueco_minutos']}")
    print(f"  el hueco de la avería es {es(payload['veces_mas_hueco_en_la_averia'], 1)} "
          f"veces el mayor de los días sanos")


if __name__ == "__main__":
    main()
