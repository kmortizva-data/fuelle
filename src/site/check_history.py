"""Before the repository goes public: everything that ever existed in it, checked.

A public repository publishes its whole history, not its last commit. A key
deleted three commits ago is still there for anyone who clones, and so is a
data file that was committed by mistake and then removed. So this does not look
at the working tree. It asks git for every blob that any commit has ever
pointed to, and checks each one once.

What it refuses:

  - any file over 10 MB, which is either data or somebody else's build output
  - anything under data/, lake/ or .venv/, which never belong in the repository
  - secrets: API keys and tokens in the shapes the common providers use
  - personal data: e-mail addresses and phone numbers
  - paths from this machine, which say more about the author than they should

It is not one of the ten checks in check_all.py: those look at the course, and
this looks at the repository. It runs before every push to the public remote.

Run:  .venv\\Scripts\\python.exe src\\site\\check_history.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
LIMITE_MB = 10

NUNCA = ("data/", "lake/", ".venv/")

# Las formas que tienen los secretos de los proveedores habituales. Mejor
# acusar de más y mirar a mano que dejar pasar uno.
SECRETOS = {
    "clave de OpenAI o Anthropic": re.compile(rb"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}"),
    "token de GitHub": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "clave de AWS": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "clave de Google": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "contraseña escrita": re.compile(rb"(?i)\b(?:password|passwd|contrase\xc3\xb1a)\s*[=:]\s*\S{4,}"),
}
CORREO = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TELEFONO = re.compile(rb"\+\d{2}[ .]?\d{3}[ .]?\d{3}[ .]?\d{3}")


def rutas_de_esta_maquina() -> re.Pattern:
    """Las rutas de esta máquina, sacadas de ella y no escritas aquí.

    La primera versión llevaba el nombre de usuario escrito en el patrón, y en
    cuanto este fichero entró en un commit la guarda se cazó a sí misma: el
    nombre que busca estaba en su propio código, que es justo lo que existe para
    impedir. Ahora el patrón se construye al correr, desde la carpeta de usuario,
    así que el nombre no aparece en ningún fichero del repositorio.
    """
    casa = Path.home()
    trozos = {casa.name, str(casa), casa.as_posix(),
              "/" + casa.as_posix().replace(":", "").lower()}
    return re.compile(b"|".join(re.escape(t.encode("utf-8")) for t in trozos if t),
                      re.IGNORECASE)


RUTAS = rutas_de_esta_maquina()

# Correos que no son de nadie: los de ejemplo, y el de la atribución de los
# commits, que es pública por diseño.
CORREOS_PERMITIDOS = {b"noreply@anthropic.com"}


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=PROJECT, check=True,
                          capture_output=True).stdout


def todos_los_blobs() -> dict[str, str]:
    """Cada blob que algún commit ha tocado, con una de las rutas que tuvo."""
    salida = {}
    for linea in git("rev-list", "--all", "--objects").decode("utf-8").splitlines():
        partes = linea.split(" ", 1)
        if len(partes) == 2:
            salida.setdefault(partes[0], partes[1])
    return salida


def main() -> None:
    blobs = todos_los_blobs()
    commits = len(git("rev-list", "--all").split())
    tamanos = {}
    entrada = "\n".join(blobs).encode("utf-8")
    info = subprocess.run(["git", "cat-file", "--batch-check"], cwd=PROJECT,
                          input=entrada, capture_output=True, check=True).stdout
    for linea in info.decode("utf-8").splitlines():
        sha, tipo, tam = linea.split()
        if tipo == "blob":
            tamanos[sha] = int(tam)

    problemas = []
    for sha, tam in tamanos.items():
        ruta = blobs[sha]
        if tam > LIMITE_MB * 1024 * 1024:
            problemas.append(f"{ruta}: {tam / 1048576:.1f} MB, más de {LIMITE_MB}")
        if ruta.startswith(NUNCA):
            problemas.append(f"{ruta}: esta carpeta no puede estar en el historial")
        if ruta.lower().endswith((".png", ".parquet", ".woff2", ".pdf")):
            continue
        contenido = git("cat-file", "blob", sha)
        for nombre, patron in SECRETOS.items():
            for hit in patron.findall(contenido):
                problemas.append(f"{ruta}: {nombre} ({hit[:12].decode('utf-8', 'replace')}...)")
        for hit in set(CORREO.findall(contenido)) - CORREOS_PERMITIDOS:
            problemas.append(f"{ruta}: correo {hit.decode('utf-8', 'replace')}")
        for hit in set(TELEFONO.findall(contenido)):
            problemas.append(f"{ruta}: teléfono {hit.decode('utf-8', 'replace')}")
        for hit in set(RUTAS.findall(contenido)):
            problemas.append(f"{ruta}: ruta de esta máquina ({hit.decode('utf-8', 'replace')})")

    print(f"  {commits} commits, {len(tamanos)} ficheros distintos en todo el historial")
    mayor = max(tamanos.items(), key=lambda kv: kv[1])
    print(f"  el mayor: {blobs[mayor[0]]}, {mayor[1] / 1048576:.2f} MB")
    print()
    if problemas:
        for p in sorted(set(problemas)):
            print(f"  {p}")
        raise SystemExit(f"{len(set(problemas))} problemas. No se publica.")
    print("Nada en el historial que no deba salir. Se puede publicar.")


if __name__ == "__main__":
    main()
