"""Calibrating the twin, and what a single observable cannot tell you. Module 26.

Module 24 measured the two rates directly from the lake. This asks the other
question: if instead of measuring them you **searched** for them, where would the
search land, and would it land in the same place?

The answer turns on something worth a module of its own. The duty cycle of a
receiver with hysteresis is

    carga = consumo / entrega

so it depends **only on the ratio** of the two parameters. Fit on the duty cycle
alone and you do not get a minimum, you get a **valley**: every pair with the
right ratio scores exactly the same, and the search has no way to prefer one.

To separate them you need a second observable, and the machine offers one for
free: **how often it starts**. The cycle takes `banda / (entrega - consumo)` to
fill plus `banda / consumo` to empty, and that time scales with the absolute
rates while the ratio stays put.

So the module fits three times, and the three surfaces are the lesson:

  1. on the duty cycle alone     -> a valley, no single answer
  2. on the starts per hour alone -> another valley, crossing the first
  3. on both                      -> one point, where the two valleys cross

Run:  .venv\\Scripts\\python.exe src\\twin\\calibrate.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from twin.model import Deposito, _crea_tramos, mide  # noqa: E402
from twin.simulate import avanza  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m26_calibrar.json"

PASO = 10 / 60          # el que salió del módulo 25
HORAS = 12              # lo que se simula en cada punto de la rejilla

# La rejilla de búsqueda, alrededor de lo que midió el módulo 24 y con sitio de
# sobra a los dos lados para que el óptimo no salga pegado a un borde.
ENTREGAS = [round(0.60 + 0.030 * i, 4) for i in range(33)]     # 0,600 a 1,560
CONSUMOS = [round(0.030 + 0.003 * i, 4) for i in range(31)]    # 0,030 a 0,120


def observado(desde: str, hasta: str) -> dict:
    """Las dos cosas que la máquina hizo y contra las que se ajusta.

    Sobre **tramos limpios**, que es la misma población con la que el módulo 24
    midió los parámetros. Contar sobre todo el registro daría una carga de 0,0608
    en vez de 0,0572, y esa diferencia no es de la máquina: es que las horas
    pegadas a un hueco no se parecen a las demás, porque al volver el registro el
    compresor está recuperando el depósito. Comparar poblaciones distintas
    convertiría eso en un error del gemelo, y no lo es.
    """
    con = duckdb.connect()
    con.execute(f"CREATE VIEW p AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet') WHERE medido")
    _crea_tramos(con, desde, hasta)
    fila = con.sql("""
        SELECT sum(CASE WHEN cargando = 1 THEN minutos ELSE 0 END) / sum(minutos),
               sum(CASE WHEN cargando = 1 THEN 1 ELSE 0 END) / (sum(minutos) / 60.0)
        FROM tramos WHERE roto = 0 AND lecturas > 1
    """).fetchone()
    con.close()
    return {"carga": round(float(fila[0]), 4),
            "arranques_por_hora": round(float(fila[1]), 3)}


def resumen(dep: Deposito) -> tuple[float, float]:
    """Lo que el gemelo hace con unos parámetros: su carga y sus arranques."""
    r = avanza(dep, dep.consumo, HORAS * 60, PASO)
    return r["carga"], r["arranques"] / HORAS


def busca(base: Deposito, obs: dict, pesa_carga: bool,
          pesa_arranques: bool) -> dict:
    """Recorre la rejilla y devuelve el mejor punto y la superficie entera."""
    superficie = []
    mejor = None
    for entrega in ENTREGAS:
        fila = []
        for consumo in CONSUMOS:
            if consumo >= entrega:      # sin margen no hay ciclo que valga
                fila.append(None)
                continue
            dep = Deposito(arranca=base.arranca, para=base.para,
                           llena=entrega - consumo, consumo=consumo)
            carga, arranques = resumen(dep)
            # Errores relativos, para que las dos magnitudes pesen igual pese a
            # estar en unidades distintas: una es una fracción y la otra por hora.
            e_carga = abs(carga - obs["carga"]) / obs["carga"]
            e_arr = abs(arranques - obs["arranques_por_hora"]) / obs["arranques_por_hora"]
            error = (e_carga if pesa_carga else 0) + (e_arr if pesa_arranques else 0)
            fila.append(round(error, 5))
            if mejor is None or error < mejor["error"]:
                mejor = {"entrega": entrega, "consumo": consumo,
                         "error": error, "carga": round(carga, 4),
                         "arranques_por_hora": round(arranques, 3),
                         # El desglose importa: un error total pequeño puede
                         # esconder que una de las dos cosas sigue muy mal.
                         "error_carga": round(e_carga, 4),
                         "error_arranques": round(e_arr, 4),
                         # Lo que el ajuste está afirmando sobre el depósito, y
                         # que el registro de presión midió directamente.
                         "sube_por_minuto_cargando": round(entrega - consumo, 4)}
        superficie.append(fila)
    mejor["error"] = round(mejor["error"], 5)
    return {"mejor": mejor, "superficie": superficie}


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    medido, contexto = mide()
    desde, hasta = contexto["ventana_sana"]
    obs = observado(desde, hasta)
    carga_medida, arranques_medidos = resumen(medido)

    print(f"  la máquina, del {desde} al {hasta}:")
    print(f"    carga              {obs['carga']:.4f}")
    print(f"    arranques por hora {obs['arranques_por_hora']:.3f}")
    print()
    print(f"  el gemelo con los parámetros MEDIDOS "
          f"(entrega {medido.entrega:.4f}, consumo {medido.consumo}):")
    print(f"    carga              {carga_medida:.4f}   "
          f"({abs(carga_medida - obs['carga']) / obs['carga']:.1%} de error)")
    print(f"    arranques por hora {arranques_medidos:.3f}   "
          f"({abs(arranques_medidos - obs['arranques_por_hora']) / obs['arranques_por_hora']:.1%})")

    print()
    print("  y ahora buscándolos, con tres objetivos distintos:")
    ajustes = {}
    for nombre, (c, a) in {"solo la carga": (True, False),
                           "solo los arranques": (False, True),
                           "las dos cosas": (True, True)}.items():
        r = busca(medido, obs, c, a)
        ajustes[nombre] = r
        m = r["mejor"]
        print(f"    {nombre:<20} entrega {m['entrega']:.3f}  consumo {m['consumo']:.4f}  "
              f"cociente {m['consumo'] / m['entrega']:.4f}  error {m['error']:.4f}")

    # Los puntos que empatan con el mejor. Su NÚMERO dice si hay valle, y el
    # rango de entregas que abarcan dice cuánto de ancho es: eso es lo que
    # convierte «no identificable» en una cifra que se puede publicar.
    empates, rangos = {}, {}
    for nombre, r in ajustes.items():
        mejor = r["mejor"]["error"]
        atados = [(ENTREGAS[i], CONSUMOS[j])
                  for i, fila in enumerate(r["superficie"])
                  for j, v in enumerate(fila)
                  if v is not None and v <= mejor + 0.002]
        empates[nombre] = len(atados)
        rangos[nombre] = {
            "entrega_min": min(e for e, _ in atados),
            "entrega_max": max(e for e, _ in atados),
            "cociente_min": round(min(c / e for e, c in atados), 4),
            "cociente_max": round(max(c / e for e, c in atados), 4),
        }
    print()
    print("  puntos que empatan con el mejor (dentro de 0,002), y qué abarcan:")
    for nombre, n in empates.items():
        r = rangos[nombre]
        print(f"    {nombre:<20} {n:>4} puntos   entrega de {r['entrega_min']:.3f} a "
              f"{r['entrega_max']:.3f}   cociente de {r['cociente_min']} a "
              f"{r['cociente_max']}")

    # El resultado del módulo, y no es el que se esperaba. El ajuste gana en el
    # marcador, así que hay que preguntarle qué está afirmando para ganarlo: su
    # depósito sube mucho más rápido de lo que el registro de presión enseña.
    ganador = ajustes["las dos cosas"]["mejor"]
    # Si el óptimo del ajuste completo cae en el borde, la rejilla es la que manda
    # y no los datos. Pasó a la primera: el mejor punto salía justo en 1,200, que
    # era el tope de entonces.
    #
    # Solo se le exige al ajuste completo, y la razón es la lección del módulo:
    # **un valle no tiene mínimo interior**, así que los otros dos siempre van a
    # acabar en un borde, le des la rejilla que le des. Que se peguen al borde no
    # es un fallo de la rejilla, es la firma de que no hay un único mejor punto.
    if ganador["entrega"] in (ENTREGAS[0], ENTREGAS[-1]) or             ganador["consumo"] in (CONSUMOS[0], CONSUMOS[-1]):
        raise SystemExit(
            f"El ajuste completo se pega al borde de la rejilla "
            f"(entrega {ganador['entrega']}, consumo {ganador['consumo']}). Lo que "
            "manda es el borde, no los datos: hay que ensancharla.")
    sube_ajustado = ganador["sube_por_minuto_cargando"]
    print()
    print("  y lo que el ajuste afirma del depósito, contra lo que se midió:")
    print(f"    sube por minuto cargando, medido   {medido.llena:.4f} bar/min")
    print(f"    sube por minuto cargando, ajustado {sube_ajustado:.4f} bar/min   "
          f"({sube_ajustado / medido.llena - 1:+.1%})")
    print(f"    error total, con los medidos       "
          f"{abs(carga_medida - obs['carga']) / obs['carga'] + abs(arranques_medidos - obs['arranques_por_hora']) / obs['arranques_por_hora']:.4f}")
    print(f"    error total, con los ajustados     {ganador['error']:.4f}")

    payload = {
        "ventana_sana": [desde, hasta],
        "observado": obs,
        "medido": {"entrega": round(medido.entrega, 4), "consumo": medido.consumo,
                   "cociente": round(medido.consumo / medido.entrega, 4),
                   "carga": round(carga_medida, 4),
                   "arranques_por_hora": round(arranques_medidos, 3)},
        "ajustado": ganador,
        "empates": empates,
        "rangos_de_empate": rangos,
        # Lo que hay que mirar para no dar por bueno el ajuste solo porque puntúa
        # mejor: cuánto sube el marcador y cuánto miente sobre el depósito.
        "error_total_medido": round(
            abs(carga_medida - obs["carga"]) / obs["carga"]
            + abs(arranques_medidos - obs["arranques_por_hora"])
            / obs["arranques_por_hora"], 4),
        "error_total_ajustado": ganador["error"],
        "sube_medido": medido.llena,
        "sube_ajustado": sube_ajustado,
        "el_ajuste_infla_el_llenado": round(sube_ajustado / medido.llena - 1, 3),
        # En tanto por ciento, porque es como se cita en la prosa y la puerta
        # de números compara la cifra escrita y no la fracción.
        "el_ajuste_infla_el_llenado_pct": round(
            (sube_ajustado / medido.llena - 1) * 100, 1),
        "puntos_de_la_rejilla": len(ENTREGAS) * len(CONSUMOS),
        "entregas": ENTREGAS,
        "consumos": CONSUMOS,
        "superficies": {k: v["superficie"] for k, v in ajustes.items()},
        "mejores": {k: v["mejor"] for k, v in ajustes.items()},
        # Lo que separa a la medida del ajuste, que es el resultado del módulo.
        "el_ajuste_sube_la_entrega": round(
            ganador["entrega"] / medido.entrega - 1, 3),
        "el_cociente_apenas_se_mueve": round(
            abs(ganador["consumo"] / ganador["entrega"]
                - medido.consumo / medido.entrega), 4),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
