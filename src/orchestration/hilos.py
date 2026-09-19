"""Does DuckDB write the same bytes twice? Module 29's finding, as an experiment.

The first rebuild of the lake brought back the same rows in different files.
This runs that finding on purpose, so the lesson can show it instead of telling
it: bronze and silver are each written twice with DuckDB's default threads and
twice with one, into a scratch folder that is deleted at the end, and then the
files and the hourly averages are compared.

Silver is also written with and without time order, because the first rebuild
turned out to have two causes mixed together: the order of the rows and the
number of threads writing them.

What it measures, for each layer and each setting:

  - how many files each write leaves, and how many come out byte identical
  - how many megabytes the layer takes
  - for silver, how many of the 4,416 hourly oil averages differ between the
    two writes once rounded to two decimals, which is what `oro_horas` does

The counts with several threads change from one run to the next: that is the
finding. The lesson quotes them from its output block, where a single run
belongs, and speaks of the conclusion in the prose.

Run:  .venv\\Scripts\\python.exe src\\orchestration\\hilos.py
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import duckdb  # noqa: E402

from ingest import bronze  # noqa: E402
from transform import silver  # noqa: E402

ZONA = PROJECT / "lake" / "_hilos"
RESULTS = PROJECT / "results" / "m29_hilos.json"
BRONCE_REAL = bronze.BRONZE

MEDIA_POR_HORA = """
    SELECT date_trunc('hour', timestamp) AS hora, round(avg(Oil_temperature), 2) AS aceite
    FROM read_parquet('{}/**/*.parquet') WHERE medido GROUP BY hora
"""


def huellas(carpeta: Path) -> dict[str, str]:
    return {f.relative_to(carpeta).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in carpeta.rglob("*.parquet")}


def mb(carpeta: Path) -> float:
    return round(sum(f.stat().st_size for f in carpeta.rglob("*.parquet")) / 1024 / 1024, 2)


def escribe(capa: str, destino: Path, varios_hilos: bool, ordenada: bool = True) -> None:
    """Una escritura de la capa, con los hilos de DuckDB o con uno solo.

    Con varios se desactiva un momento el `un_solo_hilo` de las funciones de
    verdad, sustituyéndolo por uno que no hace nada: así se escribe con el mismo
    código que el lago, cambiando solo lo que se quiere medir.
    """
    import contextlib

    from escritura import un_solo_hilo

    nada = contextlib.nullcontext
    # DuckDB no crea la carpeta madre de un COPY por particiones. En el lago lo
    # hace bronze.clear(), que aquí no se llama.
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    if capa == "bronce":
        bronze.BRONZE = destino
        bronze.un_solo_hilo = (lambda c: nada()) if varios_hilos else un_solo_hilo
        bronze.write(con)
    else:
        silver.SILVER = destino
        silver.un_solo_hilo = (lambda c: nada()) if varios_hilos else un_solo_hilo
        con.execute(f"CREATE VIEW bronce AS "
                    f"SELECT * FROM read_parquet('{BRONCE_REAL.as_posix()}/**/*.parquet')")
        borde = con.sql("SELECT min(timestamp), max(timestamp) FROM bronce").fetchone()
        silver.escribe(con, borde, ordenada)
    con.close()


def main() -> None:
    if not BRONCE_REAL.exists():
        raise SystemExit("Falta el bronce. Corre la reconstrucción o src/ingest/bronze.py.")
    shutil.rmtree(ZONA, ignore_errors=True)
    salida = {}
    try:
        casos = [("bronce", True, True), ("bronce", False, True),
                 ("plata", True, False), ("plata", False, False),
                 ("plata", True, True), ("plata", False, True)]
        for capa, varios, ordenada in casos:
            modo = ("varios hilos" if varios else "un hilo") + (
                "" if capa == "bronce" else (", en orden" if ordenada else ", sin orden"))
            a = ZONA / f"{capa}_{varios}_{ordenada}_1"
            b = ZONA / f"{capa}_{varios}_{ordenada}_2"
            escribe(capa, a, varios, ordenada)
            escribe(capa, b, varios, ordenada)
            ha, hb = huellas(a), huellas(b)
            caso = {
                "ficheros_primera": len(ha),
                "ficheros_segunda": len(hb),
                "identicos": sum(1 for k, v in ha.items() if hb.get(k) == v),
                "mb": mb(a),
            }
            if capa == "plata":
                con = duckdb.connect()
                uno = dict(con.sql(MEDIA_POR_HORA.format(a.as_posix())).fetchall())
                dos = dict(con.sql(MEDIA_POR_HORA.format(b.as_posix())).fetchall())
                con.close()
                caso["horas"] = len(uno)
                caso["horas_distintas"] = sum(1 for h in uno if uno[h] != dos.get(h))
            salida.setdefault(capa, {})[modo] = caso
            extra = (f", {caso['horas_distintas']} de {caso['horas']} medias horarias "
                     f"distintas" if capa == "plata" else "")
            print(f"  {capa:<7}{modo:<25}{caso['ficheros_primera']:>4} y "
                  f"{caso['ficheros_segunda']:>4} ficheros, {caso['identicos']:>4} idénticos, "
                  f"{caso['mb']:>6.2f} MB{extra}")
    finally:
        shutil.rmtree(ZONA, ignore_errors=True)

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=2)
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que escribe el lago de verdad: el bronce con un hilo, la plata en orden
    # y con un hilo. Eso tiene que salir idéntico, o el lago no es determinista.
    del_lago = [salida["bronce"]["un hilo"], salida["plata"]["un hilo, en orden"]]
    if any(c["identicos"] != c["ficheros_primera"] or c["ficheros_primera"] != c["ficheros_segunda"]
           for c in del_lago) or salida["plata"]["un hilo, en orden"]["horas_distintas"]:
        raise SystemExit("Con un hilo tampoco sale igual. La escritura del lago no es determinista.")


if __name__ == "__main__":
    main()
