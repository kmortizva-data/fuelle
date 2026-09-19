"""The one place that starts and stops this course's PostgreSQL. Part 5.

Until module 18 the database was a file. From module 19 it is a **service**: a
process that has to be running before anybody can ask it anything, that serves
several clients at once, and that keeps running after your script exits. That
last part is why this module exists in a single place instead of copy pasted:
a server nobody stopped is a process left behind.

**It is portable and it needs no administrator.** The official installer wants
admin rights and leaves a Windows service running; the same binaries also come
as a zip, and those run from anywhere. This project keeps them in
`~/tools/pgsql`, next to the ffmpeg and Tectonic it already uses that way.

Two deliberate choices, both visible in `postgresql.conf`:

  - **Port 5433**, not the standard 5432, so a real PostgreSQL installed later
    can live alongside this one without either noticing.
  - **`listen_addresses = 'localhost'`**, so the instance is never reachable
    from the network. Authentication is `trust`, which is only defensible
    because of that line: nothing outside this machine can open a connection.
    Module 22 replaces it with roles that actually mean something.

Uso desde cualquier script:

    from db.servidor import servidor, conecta

    with servidor():
        with conecta() as con:
            ...

Uso a mano:

    .venv\\Scripts\\python.exe src\\db\\servidor.py estado
    .venv\\Scripts\\python.exe src\\db\\servidor.py arranca
    .venv\\Scripts\\python.exe src\\db\\servidor.py para
"""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BIN = Path.home() / "tools" / "pgsql" / "bin"
DATOS = PROJECT / "lake" / "pg"
REGISTRO = DATOS / "servidor.log"

PUERTO = 5433
USUARIO = "fuelle"
BASE = "fuelle"

COMO_INSTALARLO = (
    "Falta PostgreSQL portable en ~/tools/pgsql.\n"
    "  1. Baja postgresql-17.6-1-windows-x64-binaries.zip de get.enterprisedb.com\n"
    "  2. Descomprímelo en ~/tools, que deja ~/tools/pgsql/bin\n"
    "  3. Corre src/db/servidor.py arranca\n"
    "No hace falta administrador y no deja ningún servicio."
)


def _exe(nombre: str) -> Path:
    ruta = BIN / f"{nombre}.exe"
    if not ruta.exists():
        raise SystemExit(COMO_INSTALARLO)
    return ruta


def _pg_ctl(*args: str, capturar: bool = True) -> subprocess.CompletedProcess:
    """pg_ctl, capturando la salida salvo cuando arranca.

    `capturar=False` en el arranque, y cuesta explicarlo pero no es opcional:
    `pg_ctl start` lanza `postgres.exe` como hijo, el hijo **hereda la tubería**
    de la captura, y esa tubería no se cierra nunca porque el servidor se queda
    vivo. `subprocess.run` espera el fin de fichero para siempre y el script no
    vuelve. Con la salida a DEVNULL no hay tubería que esperar, y el registro del
    servidor ya va a su fichero por `-l`.
    """
    silencio = subprocess.DEVNULL
    if capturar:
        return subprocess.run([str(_exe("pg_ctl")), "-D", str(DATOS), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
    return subprocess.run([str(_exe("pg_ctl")), "-D", str(DATOS), *args],
                          stdout=silencio, stderr=silencio, stdin=silencio)


def esta_vivo() -> bool:
    """Si el proceso existe. NO quiere decir que ya atienda."""
    return _pg_ctl("status").returncode == 0


def acepta_conexiones() -> bool:
    """Si además ya se le puede preguntar algo.

    Son dos cosas distintas y confundirlas cuesta un rato: recién arrancado, el
    proceso existe y `pg_ctl status` dice que sí, pero la base todavía está
    recuperándose y contesta «the database system is starting up». Esperar por
    `status` deja al script conectando demasiado pronto.
    """
    return subprocess.run(
        [str(_exe("pg_isready")), "-h", "localhost", "-p", str(PUERTO)],
        capture_output=True).returncode == 0


# Las tres líneas que este curso cambia en `postgresql.conf`. Todo lo demás es lo
# que deja `initdb`. Viven aquí para que un clúster rehecho desde cero, que es lo
# que hace el módulo 29, salga igual que el que se montó a mano en el 19.
AJUSTES = ("listen_addresses = 'localhost'", f"port = {PUERTO}", "lc_messages = 'C'")


def crea_cluster() -> bool:
    """El directorio de datos desde cero, si no existe. Devuelve si lo ha creado.

    Hasta el módulo 29 esto se hacía a mano una sola vez. Reconstruir el lago
    entero borra también `lake/pg`, así que el orquestador tiene que saber
    hacerlo, y la única forma de que salga igual es que lo haga siempre lo mismo.
    """
    if DATOS.exists():
        return False
    r = subprocess.run(
        [str(_exe("initdb")), "-D", str(DATOS), "-U", USUARIO,
         "--encoding=UTF8", "--locale=C", "--auth=trust"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"initdb falló: {(r.stderr or r.stdout)[-300:]}")
    lineas = ["", "# Lo que cambia este curso, desde src/db/servidor.py", *AJUSTES, ""]
    with open(DATOS / "postgresql.conf", "a", encoding="utf-8") as fh:
        fh.write("\n".join(lineas))
    return True


def arranca(espera: float = 20.0) -> bool:
    """Levanta el servidor si hace falta. Devuelve si lo ha levantado él."""
    if acepta_conexiones():
        return False
    if not DATOS.exists():
        raise SystemExit(
            f"Falta el directorio de datos {DATOS.relative_to(PROJECT)}. Créalo con:\n"
            f"  {BIN / 'initdb.exe'} -D lake/pg -U {USUARIO} "
            f"--encoding=UTF8 --locale=C --auth=trust")
    _pg_ctl("-l", str(REGISTRO), "-w", f"-t{int(espera)}", "start", capturar=False)
    limite = time.time() + espera
    while time.time() < limite:
        if acepta_conexiones():
            return True
        time.sleep(0.3)
    raise SystemExit(f"El servidor no arrancó. Mira {REGISTRO.relative_to(PROJECT)}")


def para() -> None:
    if esta_vivo():
        _pg_ctl("-w", "-m", "fast", "stop")


@contextlib.contextmanager
def servidor():
    """Arranca si hace falta, y **para solo si lo arrancó él**.

    Esa condición importa: si alguien dejó el servidor corriendo a propósito
    para trastear con psql, un script que lo pare al terminar se lo tira debajo.
    """
    lo_arranque = arranca()
    try:
        yield
    finally:
        if lo_arranque:
            para()


def conecta(base: str = BASE, usuario: str = USUARIO, autocommit: bool = False):
    """Una conexión a la base del curso, creándola la primera vez."""
    import psycopg

    dsn = f"host=localhost port={PUERTO} user={usuario} dbname={base}"
    try:
        return psycopg.connect(dsn, autocommit=autocommit)
    except psycopg.OperationalError as e:
        if "does not exist" not in str(e) and "no existe" not in str(e):
            raise
        with psycopg.connect(f"host=localhost port={PUERTO} user={usuario} "
                             f"dbname=postgres", autocommit=True) as admin:
            admin.execute(f'CREATE DATABASE "{base}"')
        print(f"  creada la base «{base}»")
        return psycopg.connect(dsn, autocommit=autocommit)


def main() -> None:
    orden = sys.argv[1] if len(sys.argv) > 1 else "estado"
    if orden == "arranca":
        nuevo = arranca()
        print(f"  servidor {'arrancado' if nuevo else 'ya estaba en marcha'} "
              f"en localhost:{PUERTO}")
    elif orden == "para":
        vivo = esta_vivo()
        para()
        print(f"  servidor {'parado' if vivo else 'ya estaba parado'}")
    elif orden == "estado":
        if not esta_vivo():
            print(f"  servidor parado. Datos en {DATOS.relative_to(PROJECT)}")
            return
        with servidor(), conecta() as con:
            version = con.execute("SELECT version()").fetchone()[0]
        print(f"  en marcha en localhost:{PUERTO}")
        print(f"  {version.split(',')[0]}")
    else:
        raise SystemExit("Órdenes: estado, arranca, para")


if __name__ == "__main__":
    main()
