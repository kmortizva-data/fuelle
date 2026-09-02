"""Who gets in, and a backup that gets restored. Module 22.

Two jobs a file never had, and the second one is the module's title: **a backup
nobody has restored is not a backup.** So this does not stop at running pg_dump.
It restores the dump into a second database and then checks the two hold the
same thing, by count and by fingerprint, table by table.

Checking is the point. A dump that runs without error and restores to something
subtly different is the worst possible outcome, because it looks like a backup
right up until the day it has to be one.

And the permissions get tested the same way as everything else on this course, by
trying: a read only role is created, and then it is asked to write. If the write
goes through, the role is decoration.

Run:  .venv\\Scripts\\python.exe src\\db\\backup.py
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.servidor import BASE, BIN, PUERTO, USUARIO, conecta, servidor  # noqa: E402
from medir import measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
COPIAS = PROJECT / "lake" / "_copias"
COPIA = COPIAS / "fuelle.dump"
RESULTS = PROJECT / "results" / "m22_copias.json"

RESTAURADA = "fuelle_restaurada"
SOLO_LECTURA = "mirona"

# La huella de cada tabla: recuento y unas sumas. No es un hash del fichero, es
# una pregunta sobre el CONTENIDO, que es lo que tiene que sobrevivir a una
# copia. Un dump y su restauración pueden diferir byte a byte y ser correctos.
HUELLAS = {
    "lecturas": """
        SELECT count(*),
               count(*) FILTER (WHERE medido),
               round(sum(oil_temperature)::numeric, 2),
               round(sum(tp2)::numeric, 2),
               count(DISTINCT day)
        FROM lecturas
    """,
    "dias": """
        SELECT count(*),
               round(sum(horas_de_carga), 2),
               sum(lecturas)
        FROM dias
    """,
}


def herramienta(nombre: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(BIN / f"{nombre}.exe"), "-h", "localhost", "-p", str(PUERTO),
         "-U", USUARIO, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**__import__("os").environ, "LC_MESSAGES": "C"})


def huellas_de(pg) -> dict:
    return {tabla: [str(v) for v in pg.execute(sql).fetchone()]
            for tabla, sql in HUELLAS.items()}


def guardas_de(pg) -> int:
    return pg.execute("""
        SELECT count(*) FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
    """).fetchone()[0]


def prueba_el_rol(pg) -> dict:
    """Crea un rol de solo lectura y comprueba que de verdad no puede escribir."""
    import psycopg

    pg.execute(f"DROP OWNED BY {SOLO_LECTURA}") if pg.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s", (SOLO_LECTURA,)
    ).fetchone() else None
    pg.execute(f"DROP ROLE IF EXISTS {SOLO_LECTURA}")
    pg.execute(f"CREATE ROLE {SOLO_LECTURA} LOGIN")
    pg.execute(f"GRANT CONNECT ON DATABASE {BASE} TO {SOLO_LECTURA}")
    pg.execute(f"GRANT USAGE ON SCHEMA public TO {SOLO_LECTURA}")
    pg.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {SOLO_LECTURA}")
    pg.commit()

    con = psycopg.connect(f"host=localhost port={PUERTO} user={SOLO_LECTURA} "
                          f"dbname={BASE}")
    leyo = con.execute("SELECT count(*) FROM lecturas").fetchone()[0]
    try:
        con.execute("DELETE FROM lecturas WHERE day = DATE '2020-06-05'")
        con.commit()
        escribio, error = True, None
    except psycopg.errors.Error as e:
        con.rollback()
        escribio, error = False, str(e).splitlines()[0].strip()
    con.close()
    return {"lee": leyo, "puede_escribir": escribio, "error": error}


def main() -> None:
    with servidor():
        pg = conecta(autocommit=True)
        if not pg.execute("SELECT to_regclass('lecturas') IS NOT NULL").fetchone()[0]:
            raise SystemExit("Falta la tabla «lecturas». Corre src/db/load_silver.py "
                             "y src/db/schema.py")

        # --- Quién entra y a qué -----------------------------------------
        print("  un rol de solo lectura, y se le pide que borre:")
        rol = prueba_el_rol(pg)
        print(f"    lee {rol['lee']:,} filas")
        print(f"    {'ESCRIBE, el rol no sirve' if rol['puede_escribir'] else 'no puede escribir'}")
        if rol["error"]:
            print(f"    {rol['error'][:96]}")

        original = huellas_de(pg)
        guardas = guardas_de(pg)

        # --- La copia -----------------------------------------------------
        COPIAS.mkdir(parents=True, exist_ok=True)
        print()
        print("  midiendo la copia y la restauración, mediana de siete:")

        def copia() -> None:
            COPIA.unlink(missing_ok=True)
            r = herramienta("pg_dump", "-d", BASE, "-Fc", "-f", str(COPIA))
            if r.returncode:
                raise SystemExit(f"pg_dump falló: {r.stderr[:200]}")

        copiar = measure(copia, runs=3)
        mb = COPIA.stat().st_size / 1024 / 1024
        print(f"    copiar      {copiar.median:.1f} s   ->  {mb:.1f} MB")

        # --- Y la restauración, que es la parte que casi nadie hace -------
        def restaura() -> None:
            pg.execute(f'DROP DATABASE IF EXISTS "{RESTAURADA}" WITH (FORCE)')
            pg.execute(f'CREATE DATABASE "{RESTAURADA}"')
            r = herramienta("pg_restore", "-d", RESTAURADA, str(COPIA))
            if r.returncode:
                raise SystemExit(f"pg_restore falló: {r.stderr[:300]}")

        restaurar = measure(restaura, runs=3)
        print(f"    restaurar   {restaurar.median:.1f} s")

        # --- La comprobación que convierte esto en una copia ---------------
        copia_pg = conecta(base=RESTAURADA)
        restaurado = huellas_de(copia_pg)
        guardas_restauradas = guardas_de(copia_pg)
        copia_pg.close()

        print()
        print("  y ahora la única prueba que vale:")
        iguales = True
        for tabla in HUELLAS:
            casa = original[tabla] == restaurado[tabla]
            iguales &= casa
            print(f"    {'igual   ' if casa else 'DISTINTA'} {tabla}: "
                  f"{', '.join(original[tabla])}")
            if not casa:
                print(f"             restaurada: {', '.join(restaurado[tabla])}")
        guardas_iguales = guardas == guardas_restauradas
        print(f"    {'igual   ' if guardas_iguales else 'DISTINTA'} las guardas: "
              f"{guardas} contra {guardas_restauradas}")

        payload = {
            "rol_de_solo_lectura": rol,
            "mb_de_la_copia": round(mb, 1),
            "segundos_en_copiar": round(copiar.median, 1),
            "segundos_en_restaurar": round(restaurar.median, 1),
            "minutos_en_restaurar": round(restaurar.median / 60, 2),
            "guardas": guardas,
            "guardas_restauradas": guardas_restauradas,
            "huellas": original,
            "huellas_restauradas": restaurado,
            "la_copia_restaura_igual": bool(iguales and guardas_iguales),
        }
        RESULTS.parent.mkdir(exist_ok=True)
        with io.open(RESULTS, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print()
        print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

        pg.execute(f'DROP DATABASE IF EXISTS "{RESTAURADA}" WITH (FORCE)')
        pg.close()

        if rol["puede_escribir"]:
            raise SystemExit("El rol de solo lectura ha podido borrar. No es de solo lectura.")
        if not (iguales and guardas_iguales):
            raise SystemExit("La copia no restaura lo mismo. Eso no es una copia.")


if __name__ == "__main__":
    main()
