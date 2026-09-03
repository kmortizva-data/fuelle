"""Stepping the twin through time, and what the step size costs. Module 25.

The model from `model.py` says how fast the receiver fills and empties. Turning
that into a run means advancing it a little at a time, and **the size of that
little decides the answer**. Too coarse and the simulation walks past the
pressure switch without noticing it, so the cycles come out wrong.

So the step is not chosen, it is measured: the same eight hours get simulated at
a range of step sizes and each is compared against the finest one. The step to
use is the coarsest whose answer still agrees.

This also writes the knob data the lessons use. **The physics is simulated here,
in Python, once per knob position**, and the page only swaps series. That is
deliberate: writing it a second time in JavaScript would mean two implementations
that can drift apart, and there is no JavaScript runtime on this machine to check
them against each other. One implementation cannot disagree with itself.

Run:  .venv\\Scripts\\python.exe src\\twin\\simulate.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from twin.model import Deposito, mide  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
PERILLAS = PROJECT / "assets" / "perillas"
RESULTS = PROJECT / "results" / "m25_simular.json"

# El paso más fino con el que se compara todo lo demás. Un décimo de segundo es
# doscientas veces menor que el ritmo del registro, así que sirve de patrón.
PASO_FINO = 0.1 / 60          # en minutos
PASOS = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 60, 120]   # segundos

HORAS = 8

# **El criterio son los ciclos, no el ciclo de trabajo.** Es el hallazgo del
# módulo y costó una corrida verlo: con paso de 30 s la carga sale casi clavada
# a la del patrón, error de 0,00008, y ya ha perdido dos arranques de dieciséis.
# Un paso grueso da un ciclo de trabajo que parece bien mientras se salta ciclos
# enteros, y eso es el falso verde del módulo 16 aplicado a una simulación.
#
# Contar arranques no se puede equivocar así: o resuelve el ciclo o no.

# Las posiciones de las dos perillas. Van precalculadas, así que son discretas.
CONSUMOS = [round(0.02 + 0.01 * i, 3) for i in range(21)]      # bar/min
PUNTOS_DEL_TRAZO = 240


def avanza(dep: Deposito, consumo: float, minutos: float, paso: float,
           presion_inicial: float | None = None) -> dict:
    """Adelanta el depósito en el tiempo y devuelve lo que hizo.

    Es todo el gemelo. El estado es una sola variable, la presión, y la única
    decisión es la del presostato: cargar por debajo de `arranca` y soltar por
    encima de `para`. La histéresis es lo que hace que esto cicle en vez de
    quedarse pegado al umbral.
    """
    p = dep.para if presion_inicial is None else presion_inicial
    cargando = False
    cargados = 0.0
    arranques = 0
    trabajo: list[float] = []
    presiones: list[float] = []
    n = int(round(minutos / paso))

    for _ in range(n):
        if cargando:
            p += (dep.entrega - consumo) * paso
            if p >= dep.para:
                cargando = False
        else:
            p -= consumo * paso
            if p <= dep.arranca:
                cargando = True
                arranques += 1
        if cargando:
            cargados += paso
        trabajo.append(cargados)
        presiones.append(p)

    return {
        "carga": cargados / minutos if minutos else 0.0,
        "arranques": arranques,
        "minutos_cargando": cargados,
        "trabajo": trabajo,
        "presiones": presiones,
        "presion_final": p,
    }


def recorta(serie: list[float], puntos: int) -> list[float]:
    """Deja la serie en `puntos` valores, para no mandar 8.640 al navegador."""
    if len(serie) <= puntos:
        return [round(v, 2) for v in serie]
    salto = len(serie) / puntos
    return [round(serie[min(int(i * salto), len(serie) - 1)], 2) for i in range(puntos)]


def prueba_del_paso(dep: Deposito, consumo: float) -> list[dict]:
    """Simula lo mismo con pasos distintos y compara todo con el más fino."""
    patron = avanza(dep, consumo, HORAS * 60, PASO_FINO)
    fuera = []
    for segundos in PASOS:
        r = avanza(dep, consumo, HORAS * 60, segundos / 60)
        fuera.append({
            "segundos": segundos,
            "carga": round(r["carga"], 4),
            "arranques": r["arranques"],
            "error_de_carga": round(abs(r["carga"] - patron["carga"]), 5),
            "ciclos_perdidos": patron["arranques"] - r["arranques"],
            "se_parece": r["arranques"] == patron["arranques"],
        })
    return [{"segundos": "patrón", "carga": round(patron["carga"], 4),
             "arranques": patron["arranques"], "error_de_carga": 0.0,
             "ciclos_perdidos": 0, "se_parece": True}] + fuera


def perilla_consumo(dep: Deposito) -> dict:
    """Módulo 24: mover el consumo y ver al compresor cargar más seguido.

    El trazo es el **trabajo acumulado**, nunca la presión. La presión es la
    variable que el control sostiene, y ya se midió en la página de pruebas que
    dibujarla no separa nada: 32 px de distancia con 5 l/min de fuga contra 31
    con 40. La regla del curso viene de ahí.
    """
    minutos = 4 * 60
    paso = 10 / 60
    base = avanza(dep, dep.consumo, minutos, paso)
    series = []
    for consumo in CONSUMOS:
        r = avanza(dep, consumo, minutos, paso)
        series.append({
            "valor": consumo,
            "trazo": recorta(r["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(r["carga"], 4),
            "arranques": r["arranques"],
        })
    return {
        "titulo": "el consumo, y lo que el compresor tiene que hacer para sostenerlo",
        "etiqueta": "consumo",
        "unidad": "bar/min",
        "eje": "minutos cargando, acumulados",
        "horas": minutos / 60,
        "referencia": {
            "valor": dep.consumo,
            "trazo": recorta(base["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(base["carga"], 4),
            "arranques": base["arranques"],
        },
        "posiciones": series,
    }


def perilla_paso(dep: Deposito) -> dict:
    """Módulo 25: mover el paso de tiempo y ver cuándo la simulación se rompe."""
    minutos = 4 * 60
    patron = avanza(dep, dep.consumo, minutos, PASO_FINO)
    series = []
    for segundos in PASOS:
        r = avanza(dep, dep.consumo, minutos, segundos / 60)
        series.append({
            "valor": segundos,
            "trazo": recorta(r["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(r["carga"], 4),
            "arranques": r["arranques"],
        })
    return {
        "titulo": "el paso de tiempo, y a partir de cuál la simulación deja de valer",
        "etiqueta": "paso",
        "unidad": "s",
        "eje": "minutos cargando, acumulados",
        "horas": minutos / 60,
        "referencia": {
            "valor": round(PASO_FINO * 60, 1),
            "trazo": recorta(patron["trabajo"], PUNTOS_DEL_TRAZO),
            "carga": round(patron["carga"], 4),
            "arranques": patron["arranques"],
        },
        "posiciones": series,
    }


def main() -> None:
    dep, contexto = mide()
    print(f"  el gemelo, con lo que midió model.py:")
    print(f"    arranca {dep.arranca}, para {dep.para}, "
          f"entrega {dep.entrega:.3f}, consumo {dep.consumo}")

    # --- Lo primero: ¿se parece a la máquina de verdad? ------------------
    dia = avanza(dep, dep.consumo, 24 * 60, PASO_FINO)
    # Se compara contra la carga por TRAMOS y no contra la fracción de lecturas.
    # El gemelo integra tiempo, y la fracción de lecturas cuenta solo las que
    # existen: con el 18,3 % de huecos que el módulo 14 midió, esa fracción sale
    # baja por una razón que no tiene nada que ver con el modelo.
    observada = contexto["balance"]["carga_por_tramos"]
    por_lecturas = contexto["carga_observada"]
    print()
    print(f"  carga simulada       {dia['carga']:.4f}")
    print(f"  carga observada      {observada:.4f}   (por tramos, que es lo comparable)")
    print(f"  y por lecturas       {por_lecturas:.4f}   (baja por los huecos del registro)")
    print(f"  se lleva             {abs(dia['carga'] - observada) / observada:.1%}")

    # --- La prueba del paso ---------------------------------------------
    print()
    print("  el mismo turno de ocho horas, con pasos distintos:")
    tabla = prueba_del_paso(dep, dep.consumo)
    for r in tabla:
        marca = "" if r["se_parece"] else f"   pierde {r['ciclos_perdidos']} ciclos"
        print(f"    paso {str(r['segundos']):>6} s   carga {r['carga']:.4f}   "
              f"arranques {r['arranques']:>3}   error de carga "
              f"{r['error_de_carga']:.5f}{marca}")
    bueno = [r for r in tabla[1:] if r["se_parece"]]
    mayor = max((r["segundos"] for r in bueno), default=None)
    print(f"    el paso más grande que aún vale: {mayor} s")

    # --- Las dos perillas ------------------------------------------------
    PERILLAS.mkdir(parents=True, exist_ok=True)
    for nombre, datos in (("m24_consumo", perilla_consumo(dep)),
                          ("m25_paso", perilla_paso(dep))):
        destino = PERILLAS / f"{nombre}.json"
        with io.open(destino, "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"  {destino.name:<20} {len(datos['posiciones'])} posiciones, "
              f"{destino.stat().st_size / 1024:>6.1f} KB")

    payload = {
        "carga_simulada": round(dia["carga"], 4),
        "carga_observada": observada,
        "carga_observada_por_lecturas": por_lecturas,
        "error_relativo": round(abs(dia["carga"] - observada) / observada, 4),
        "arranques_simulados": dia["arranques"],
        "horas_de_la_prueba": HORAS,
        "arranques_del_patron": tabla[0]["arranques"],
        "paso_mas_grande_que_vale": mayor,
        "ritmo_del_registro_s": 10,
        "paso_patron_s": round(PASO_FINO * 60, 1),
        "pasos": tabla,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
