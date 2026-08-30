"""Ningún número se publica sin que un script lo haya calculado.

Existe porque en una sola sesión se colaron dos cifras escritas a mano y mal: las
lecturas del 13 de mayo (8.435 cuando eran 8.716) y el histograma de intervalos
del módulo 1 (174.382 cuando eran 128.277). Las dos se cazaron por casualidad.
Con treinta lecciones por delante, copiar cifras a mano sin red es una fuga
garantizada.

La regla: **todo número de la prosa tiene que existir en `results/`**, que solo
escriben los scripts al ejecutarse. Lo que no salió de una corrida no se publica.

Qué se comprueba y qué no:

  - Se comprueban los números que parecen datos: cuatro cifras o más, o con
    decimales. Un «los tres pasos» o un «módulo 16» no es un dato.
  - Los bloques de código y de salida quedan fuera: su corrección la verifica
    ejecutarlos, que es otro trabajo.
  - Las excepciones legítimas (los números redondos del ejemplo de juguete, un
    umbral que viene de la ficha del fabricante) se declaran en
    `results/permitidos.json` **con su razón escrita**. Declarar una excepción
    cuesta una línea; inventarse un dato, un fallo de credibilidad.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_numbers.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
LESSONS = PROJECT / "lecciones"
RESULTS = PROJECT / "results"
ALLOWED = RESULTS / "permitidos.json"

NUMBER = re.compile(r"\d[\d.,]*\d|\d")
# Las fechas ISO y los años se saltan enteros: son estructura, no medición.
DATE = re.compile(r"\d{4}-\d{2}(-\d{2})?")


def canonical(raw: str) -> str | None:
    """1.516.948 y 1,516,948 son el mismo número. Devuelve None si no es un dato.

    Se descartan los que no parecen medición: menos de cuatro cifras y sin
    decimales. Un «los tres pasos» o un «módulo 16» no hay que justificarlo.
    """
    body = raw.strip()
    last = max(body.rfind("."), body.rfind(","))
    if last == -1:
        return body if len(body) >= 4 else None

    tail = body[last + 1:]
    groups = re.split(r"[.,]", body)
    # Un separador de millares no puede llevar un cero solo delante: «0,003» es
    # tres milésimas, no cero mil tres. Sin esta condición el verificador pedía
    # justificar tiempos como 0,003 s que sí estaban medidos, que es la clase de
    # falso positivo que hace que una puerta deje de creerse.
    parece_millares = (len(tail) == 3
                       and all(len(g) == 3 for g in groups[1:])
                       and groups[0] != "0")
    if parece_millares:
        entero = "".join(groups)
        return entero if len(entero) >= 4 else None

    entero = re.sub(r"[.,]", "", body[:last]) or "0"
    return _trim(f"{entero}.{tail}")


def _trim(value: str) -> str:
    """10.0000 y 10.0 son el mismo numero, y 0.50 y 0.5 tambien.

    Sin esto el verificador pedia justificar un 10,0000 que results guardaba
    como 10.0, que es exactamente el falso positivo que hace que una puerta
    deje de creerse.
    """
    if "." not in value:
        return value.lstrip("0") or "0"
    entero, _, decimal = value.partition(".")
    decimal = decimal.rstrip("0")
    entero = entero.lstrip("0") or "0"
    return f"{entero}.{decimal}" if decimal else entero


# Claves cuyo valor es código, no medición. Sus números son constantes que el
# propio análisis escribió (3600 segundos por hora, 8640 lecturas por día), y
# contarlas como medidas abría un agujero: cualquier cifra que apareciese en
# algún SQL guardado pasaba la puerta sin haber sido medida jamás.
CODIGO = {"sql", "query", "consulta", "code", "codigo", "script", "scripts"}


def harvest(value, out: set, key: str | None = None) -> None:
    """Todos los números que hay dentro de un JSON, a cualquier profundidad."""
    if key and key.lower() in CODIGO:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(_trim(str(value)))
        out.add(_trim(str(round(float(value), 2))))
        out.add(_trim(str(round(float(value), 1))))
        if float(value).is_integer():
            out.add(str(int(value)))
        return
    if isinstance(value, str):
        for m in NUMBER.finditer(value):
            c = canonical(m.group())
            if c:
                out.add(c)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            harvest(v, out, k)
    elif isinstance(value, list):
        for v in value:
            harvest(v, out, key)


def measured() -> set:
    """Todo número que algún script haya escrito en results/."""
    out: set = set()
    for f in RESULTS.glob("*.json"):
        if f.name == "permitidos.json":
            continue
        harvest(json.loads(io.open(f, encoding="utf-8").read()), out)
    # El temario también cuenta: sus `_hechos_verificados` se comprobaron contra
    # el fichero original y el PDF oficial.
    temario = json.loads(io.open(PROJECT / "temario.json", encoding="utf-8").read())
    harvest(temario.get("_hechos_verificados", {}), out)
    for module in temario["modules"]:
        harvest(module.get("cifra", {}), out)
    return out


def allowed() -> dict:
    if not ALLOWED.exists():
        return {}
    return json.loads(io.open(ALLOWED, encoding="utf-8").read())


# Lo que va en negrita es lo que el autor está afirmando, así que se comprueba
# aunque sea pequeño. Sin esto, un «203 veces» inventado pasaba la puerta por
# tener solo tres cifras, y ese es justo el número que titula un módulo.
NEGRITA = re.compile(r"\*\*(.+?)\*\*", re.S)


def prose(text: str) -> list[tuple[int, str]]:
    """La prosa con su número de línea, sin bloques de código ni fechas."""
    out, inside = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            inside = not inside
            continue
        if inside:
            continue
        out.append((n, DATE.sub(" ", line)))
    return out


def clave(path: Path) -> str:
    """La clave de excepciones, con el idioma dentro.

    Las dos ediciones comparten nombre de fichero, así que sin esto una excepción
    declarada en español tapaba en silencio el mismo número en la inglesa. Cada
    edición declara las suyas y se ve cuál falta.
    """
    return path.stem + ("_en" if path.parent.name == "en" else "")


def check(path: Path, known: set, excepciones: dict) -> list[str]:
    text = io.open(path, encoding="utf-8").read()
    permitidos = excepciones.get(clave(path), {})
    problems = []
    for line_no, line in prose(text):
        destacados = {n for trozo in NEGRITA.findall(line)
                      for n in NUMBER.findall(trozo)}
        for m in NUMBER.finditer(line):
            crudo = m.group()
            value = canonical(crudo)
            if value is None and crudo in destacados:
                # Va en negrita: se afirma, así que se comprueba igual.
                value = _trim(crudo.replace(".", "").replace(",", "."))
            if value is None or value in known or value in permitidos:
                continue
            problems.append(
                f"{path.name}:{line_no}  «{m.group()}» no sale de ningún script. "
                f"Recalcúlalo, o declara la excepción en results/permitidos.json"
            )
    return problems


def main() -> None:
    known = measured()
    excepciones = allowed()
    lecciones = sorted(LESSONS.glob("m[0-9][0-9]_*.md"))
    lecciones += sorted((LESSONS / "en").glob("m[0-9][0-9]_*.md"))
    if not lecciones:
        print("  todavía no hay lecciones")
        return

    print(f"  {len(known)} números medidos en results/ y en el temario")
    problems = []
    for path in lecciones:
        found = check(path, known, excepciones)
        etiqueta = path.stem + (" (en)" if path.parent.name == "en" else "")
        print(f"  {etiqueta:<26} {'verde' if not found else f'{len(found)} sin respaldo'}")
        problems += found

    print()
    if problems:
        for problem in problems[:25]:
            print(f"  {problem}")
        if len(problems) > 25:
            print(f"  ... y {len(problems) - 25} más")
        raise SystemExit(f"{len(problems)} números sin respaldo. No commitear.")
    print("Todos los números publicados salen de una corrida.")


if __name__ == "__main__":
    main()
