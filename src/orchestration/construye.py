"""Build the whole lake with Dagster, from the raw files, in the order of the graph.

This is how a new machine gets a lake: clone the repository, download the CSV
into data/, and run this. Every group is asked of Dagster in turn, and inside
each group Dagster decides the order from what each asset declares.

reconstruye.py uses the same steps, and adds the proof around them: it sets the
existing lake aside first and compares what comes back. That one needs a lake
to exist already; this one does not.

Run:  .venv\\Scripts\\python.exe src\\orchestration\\construye.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
# Antes de importar dagster. Sin esto la telemetría va encendida: lo explica
# dagster_home/dagster.yaml.
os.environ["DAGSTER_HOME"] = str(PROJECT / "dagster_home")
sys.path.insert(0, str(PROJECT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import dagster as dg  # noqa: E402

from orchestration import definitions as d  # noqa: E402

TODO = [*d.defs.assets, *d.defs.asset_checks]
CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"


def pasos() -> list[tuple[str, str, dg.AssetSelection, dict]]:
    """Los grupos en orden. El bronce va solo y primero, porque va por días."""
    tramo = {"dagster/asset_partition_range_start": d.DIAS.get_first_partition_key(),
             "dagster/asset_partition_range_end": d.DIAS.get_last_partition_key()}
    return [
        ("lago", "el bronce, los 214 días en una corrida",
         dg.AssetSelection.assets(d.bronce), {"tags": tramo}),
        ("lago", "el resto del lago, con el oro de dbt",
         dg.AssetSelection.groups("lago") - dg.AssetSelection.assets(d.bronce), {}),
        ("lecciones", "lo que consultan las lecciones", dg.AssetSelection.groups("lecciones"), {}),
        ("gemelo", "el gemelo, de la física al veredicto", dg.AssetSelection.groups("gemelo"), {}),
        ("servidor", "PostgreSQL, desde initdb", dg.AssetSelection.groups("servidor"), {}),
    ]


def materializa(seleccion, **kw) -> tuple[float, dg.ExecuteInProcessResult]:
    t0 = time.perf_counter()
    r = dg.materialize(TODO, selection=seleccion, instance=dg.DagsterInstance.get(),
                       resources=d.defs.resources, raise_on_error=False, **kw)
    return time.perf_counter() - t0, r


def comprobaciones(r: dg.ExecuteInProcessResult) -> list[tuple[str, bool]]:
    return [(e.asset_check_key.name, e.passed) for e in r.get_asset_check_evaluations()]


def construye_todo(si_falla: str = "") -> tuple[dict[str, float], list[tuple[str, bool]]]:
    """Todos los grupos en orden. Para en el primer paso que falle, y dice cuál.

    Devuelve los segundos de cada grupo y las comprobaciones que corrió Dagster.
    `si_falla` se añade al mensaje de error, para quien llama con algo que decir.
    """
    segundos: dict[str, float] = {}
    evaluadas: list[tuple[str, bool]] = []
    for grupo, que, seleccion, extra in pasos():
        tardo, r = materializa(seleccion, **extra)
        segundos[grupo] = segundos.get(grupo, 0.0) + tardo
        evaluadas += comprobaciones(r)
        print(f"     {'bien ' if r.success else 'FALLA'} {que:<42} {tardo:6.1f} s")
        if not r.success:
            raise SystemExit(f"Un paso de Dagster ha fallado: {que}. Mira el registro de la "
                             f"corrida {r.run_id}.\n{si_falla}".rstrip())
    return segundos, evaluadas


def main() -> None:
    if not CSV.exists():
        raise SystemExit(f"Falta {CSV.relative_to(PROJECT)}. Se descarga de la UCI: "
                         "https://doi.org/10.24432/C5VW3R")
    print("  Dagster lo construye todo")
    segundos, evaluadas = construye_todo()
    en_verde = sum(1 for _, bien in evaluadas if bien)
    print(f"  {en_verde} de {len(evaluadas)} comprobaciones en verde, "
          f"{sum(segundos.values()) / 60:.1f} minutos")
    if en_verde != len(evaluadas):
        raise SystemExit("Alguna comprobación ha fallado. El lago está construido pero no "
                         "cumple lo que promete.")


if __name__ == "__main__":
    main()
