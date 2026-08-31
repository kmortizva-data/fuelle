"""A contract for the silver layer, and five ways of breaking it. Module 16.

A data contract is a set of promises about a table, written as code that runs.
Not documentation: assertions with a return code.

The module has the same shape as this project's own verifiers, and for the same
reason. **A check nobody has seen fail proves nothing.** So the script does two
things:

  1. Runs the contract against the real silver layer, which should pass.
  2. Takes a copy, breaks it five different ways, and runs the contract on each,
     which should fail five times and say why.

The five breakages are the ones that actually happen on a Monday morning:

  - a column arrives renamed
  - a column arrives in different units, pressure in millibar instead of bar
  - a new column shows up that nobody mentioned
  - a duplicated timestamp, from an ingestion that ran twice (module 5)
  - an impossible value, a negative reading count

Every one of those passes silently through a pipeline with no contract, and
every one of them ruins a number downstream.

Run:  .venv\\Scripts\\python.exe src\\transform\\contracts.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
SCRATCH = PROJECT / "lake" / "_contrato"
RESULTS = PROJECT / "results" / "m16_contrato.json"

# El contrato. Cada promesa es una consulta que tiene que devolver cero filas:
# las que devuelva son las que lo incumplen, y así el mensaje de error ya trae
# los datos culpables en vez de un «algo falla».
CONTRATO = {
    "las columnas son las acordadas": """
        SELECT 1 WHERE (
            SELECT count(*) FROM (
                SELECT column_name FROM (DESCRIBE SELECT * FROM datos)
                WHERE column_name IN {columnas}
            )
        ) <> {cuantas}
    """,
    "timestamp no se repite": """
        SELECT timestamp, count(*) AS veces FROM datos
        GROUP BY timestamp HAVING count(*) > 1
    """,
    "la presion esta en bar y no en otra unidad": """
        SELECT min(TP2) AS minimo, max(TP2) AS maximo FROM datos
        HAVING max(TP2) > 15 OR min(TP2) < -2
    """,
    "las digitales solo valen cero o uno": """
        SELECT DISTINCT COMP FROM datos
        WHERE COMP IS NOT NULL AND COMP NOT IN (0, 1)
    """,
    "el recuento de lecturas nunca es negativo": """
        SELECT timestamp, lecturas FROM datos WHERE lecturas < 0
    """,
    "el dia se corresponde con la marca de tiempo": """
        SELECT timestamp, day FROM datos WHERE day <> CAST(timestamp AS DATE)
    """,
    "una casilla sin medir no trae presion": """
        SELECT timestamp FROM datos WHERE NOT medido AND TP2 IS NOT NULL
    """,
}

# La promesa que faltaba en la primera version del contrato. Se guarda aparte
# para poder correr el contrato sin ella y con ella, porque el hallazgo del
# modulo es justo la diferencia entre las dos.
PROMESA_QUE_FALTABA = {
    "no llegan columnas de mas": """
        SELECT column_name FROM (DESCRIBE SELECT * FROM datos)
        WHERE column_name NOT IN {columnas}
    """,
}

COLUMNAS = ("timestamp", "day", "lecturas", "medido", "dudoso",
            "TP2", "TP3", "H1", "DV_pressure", "Reservoirs",
            "Oil_temperature", "Motor_current", "COMP", "DV_eletric",
            "Towers", "MPG", "LPS", "Pressure_switch", "Oil_level",
            "Caudal_impulses")

# Las cinco roturas del lunes por la mañana, cada una con la consulta que la
# provoca sobre una copia. Ninguna da error al escribirse: ese es el problema.
ROTURAS = {
    "una columna llega con otro nombre":
        "SELECT * EXCLUDE (TP2), TP2 AS presion_tp2 FROM datos",
    "la presion llega en milibares":
        "SELECT * EXCLUDE (TP2), TP2 * 1000 AS TP2 FROM datos",
    "aparece una columna que nadie anuncio":
        "SELECT *, 1 AS columna_nueva FROM datos",
    "la ingesta corrio dos veces":
        "SELECT * FROM datos UNION ALL SELECT * FROM datos WHERE lecturas > 1",
    "un recuento de lecturas negativo":
        "SELECT * EXCLUDE (lecturas), CASE WHEN medido AND dudoso THEN -1 "
        "ELSE lecturas END AS lecturas FROM datos",
}


def revisa(con: duckdb.DuckDBPyConnection, promesas: dict) -> list[tuple[str, str]]:
    """Corre el contrato y devuelve qué promesas se incumplen, y por qué.

    Una promesa que **no puede ni ejecutarse** cuenta como rota, y no como un
    fallo del contrato. Es lo que pasa cuando una columna llega con otro nombre:
    la consulta que preguntaba por ella deja de tener sentido, y eso es
    exactamente la noticia que hay que dar.
    """
    rotas = []
    for promesa, sql in promesas.items():
        consulta = sql.format(columnas=COLUMNAS, cuantas=len(COLUMNAS))
        try:
            filas = con.sql(consulta).fetchall()
        except Exception as e:
            rotas.append((promesa, f"ni se puede comprobar: {str(e).splitlines()[0][:60]}"))
            continue
        if filas:
            rotas.append((promesa, f"{len(filas):,} filas la incumplen"))
    return rotas


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW datos AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")

    completo = {**CONTRATO, **PROMESA_QUE_FALTABA}

    # 1. El contrato sobre la capa de verdad.
    rotas = revisa(con, completo)
    print(f"  el contrato tiene {len(completo)} promesas")
    print(f"  sobre la plata de verdad se incumplen: {len(rotas)}")
    for promesa, porque in rotas:
        print(f"    ROTA  {promesa}: {porque}")

    # 2. Las cinco roturas, cada una sobre su copia.
    #
    #    Sin esto el contrato sería una lista de buenas intenciones. Un contrato
    #    que nunca se ha visto fallar no protege de nada, igual que la huella del
    #    módulo 5 y que los verificadores de este curso.
    print()
    print("  y ahora, rompiéndolo a propósito:")
    resultados = []
    for rotura, sql in ROTURAS.items():
        roto = duckdb.connect()
        roto.execute(f"CREATE VIEW plata AS "
                     f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")
        roto.execute(f"CREATE VIEW datos AS {sql.replace('FROM datos', 'FROM plata')}")
        primera = revisa(roto, CONTRATO)
        cazada = revisa(roto, completo)
        resultados.append({
            "rotura": rotura,
            "la_caza_la_primera_version": bool(primera),
            "la_caza": bool(cazada),
            "promesas_rotas": [p for p, _ in cazada],
        })
        marca = "la caza" if cazada else "SE ESCAPA"
        aviso = "" if primera else "   (la primera versión la dejaba pasar)"
        print(f"    {marca:<10} {rotura}{aviso}")
        for promesa, porque in cazada:
            print(f"                 «{promesa}»: {porque}")
        roto.close()

    cazadas = sum(1 for r in resultados if r["la_caza"])
    cazadas_antes = sum(1 for r in resultados if r["la_caza_la_primera_version"])
    payload = {
        "promesas": len(completo),
        "promesas_de_la_primera_version": len(CONTRATO),
        "promesas_del_contrato": list(completo),
        "roturas_cazadas_por_la_primera_version": cazadas_antes,
        "columnas_acordadas": len(COLUMNAS),
        "rotas_en_la_plata": len(rotas),
        "roturas_probadas": len(ROTURAS),
        "roturas_cazadas": cazadas,
        "detalle": resultados,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  la primera versión, con {len(CONTRATO)} promesas, cazaba "
          f"{cazadas_antes} de {len(ROTURAS)}")
    print(f"  con la promesa que faltaba, {len(completo)} promesas, caza "
          f"{cazadas} de {len(ROTURAS)}")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")
    shutil.rmtree(SCRATCH, ignore_errors=True)

    if rotas:
        raise SystemExit("La plata incumple su propio contrato. Eso es un fallo de la capa.")
    if cazadas != len(ROTURAS):
        escapadas = [r["rotura"] for r in resultados if not r["la_caza"]]
        raise SystemExit(f"El contrato deja pasar {len(escapadas)}: {', '.join(escapadas)}. "
                         "Una promesa que no se ha visto fallar no protege de nada.")


if __name__ == "__main__":
    main()
