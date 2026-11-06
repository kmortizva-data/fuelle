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


def canonical(raw: str, lang: str = "es") -> str | None:
    """1.516.948 y 1,516,948 son el mismo número. Devuelve None si no es un dato.

    Se descartan los que no parecen medición: menos de cuatro cifras y sin
    decimales. Un «los tres pasos» o un «módulo 16» no hay que justificarlo.

    **El idioma decide cuál es el separador decimal**, y no el número de cifras.
    En español la coma es el decimal y el punto el de millares; en inglés al
    revés. Adivinarlo contando cifras leía «8,198» como ocho mil ciento noventa
    y ocho, así que un valor de tres decimales publicado en una lección española
    no había forma de declararlo: la excepción y la prosa nunca coincidían.
    """
    body = raw.strip()
    decimal, millares = (",", ".") if lang == "es" else (".", ",")

    last = body.rfind(decimal)
    if last != -1:
        # Hay separador decimal: lo de después son decimales, sin discusión.
        entero = body[:last].replace(millares, "") or "0"
        return _trim(f"{entero}.{body[last + 1:]}")

    if millares not in body:
        return body if len(body) >= 4 else None

    # Solo hay separadores de millares. Se comprueba que lo parezcan de verdad:
    # un «0.003» inglés no es cero mil tres, es tres milésimas mal escritas, y
    # eso es un error de la lección, no un número que haya que canonizar.
    groups = body.split(millares)
    if all(len(g) == 3 for g in groups[1:]) and groups[0] not in ("0", ""):
        entero = "".join(groups)
        return entero if len(entero) >= 4 else None
    return _trim(f"{groups[0]}.{''.join(groups[1:])}")


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
    # La edición inglesa escribe 1,516,948 y 3.42; la española al revés. Sin
    # esto, cada número de tres decimales se leía como millares en la mitad de
    # las lecciones.
    lang = "en" if path.parent.name == "en" else "es"
    # Las excepciones se declaran como se escriben, y se comparan canonizadas.
    permitidos = {canonical(k, "en") or k: v for k, v in permitidos.items()}
    problems = []
    for line_no, line in prose(text):
        destacados = {n for trozo in NEGRITA.findall(line)
                      for n in NUMBER.findall(trozo)}
        for m in NUMBER.finditer(line):
            crudo = m.group()
            value = canonical(crudo, lang)
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


# La cabecera de cada lección, en los dos idiomas.
RESUMEN = re.compile(r"^## (?:En 30 segundos|In 30 seconds)\n(.*?)^## ", re.S | re.M)
# «dos partes numerados `#1`»: una etiqueta, no una cantidad.
ETIQUETA = re.compile(r"#\d+")


def own_numbers(module: int, temario: dict) -> set:
    """Los números que puede citar la cabecera de un módulo: los de SUS resultados.

    Con el redondeo a entero incluido, porque la cabecera resume («unos 20 s»
    por 19,3, «95 veces» por 95,4), y con los hechos verificados del temario.
    """
    out: set = set()
    for f in RESULTS.glob(f"m{module:02d}_*.json"):
        harvest(json.loads(io.open(f, encoding="utf-8").read()), out)
    out |= {str(round(float(v))) for v in list(out) if re.fullmatch(r"\d+\.\d+", v)}
    harvest(temario.get("_hechos_verificados", {}), out)
    module_entry = next((m for m in temario["modules"] if m["number"] == module), {})
    harvest(module_entry.get("cifra", {}), out)
    return out


def headline(path: Path, temario: dict, excepciones: dict) -> list[str]:
    """La negrita del «En 30 segundos» tiene que salir de los resultados de SU módulo.

    La regla general mira si el número existe en algún fichero de results/, y
    un «25» existe en muchos. Así pasó la puerta el resumen del módulo 7, que
    decía «de 54 veces a 25» cuando su propio JSON dice 21,6 (22 redondeado):
    el 25 era de otra corrida. La cabecera es lo que más se lee y lo que menos se
    revisa, así que aquí la vara es más estrecha. Medido antes de activarla: con
    el redondeo a entero, los hechos del temario y las etiquetas `#N` fuera, las
    62 lecciones pasan, y con el 25 de vuelta en el 7 caza las dos ediciones.
    """
    text = io.open(path, encoding="utf-8").read()
    section = RESUMEN.search(text)
    if not section:
        return []
    lang = "en" if path.parent.name == "en" else "es"
    own = own_numbers(int(path.name[1:3]), temario)
    permitidos = {canonical(k, "en") or k
                  for k in excepciones.get(clave(path), {})}
    problems = []
    for trozo in NEGRITA.findall(section.group(1)):
        for m in NUMBER.finditer(ETIQUETA.sub(" ", DATE.sub(" ", trozo))):
            crudo = m.group()
            value = (canonical(crudo, lang)
                     or _trim(crudo.replace(".", "").replace(",", ".") if lang == "es"
                              else crudo.replace(",", "")))
            if value in own or value in permitidos:
                continue
            problems.append(
                f"{path.name}  «{crudo}» en el resumen no sale de los resultados de "
                f"su módulo (results/m{path.name[1:3]}_*.json)"
            )
    return problems


def main() -> None:
    known = measured()
    temario = json.loads(io.open(PROJECT / "temario.json", encoding="utf-8").read())
    excepciones = allowed()
    lecciones = sorted(LESSONS.glob("m[0-9][0-9]_*.md"))
    lecciones += sorted((LESSONS / "en").glob("m[0-9][0-9]_*.md"))
    if not lecciones:
        print("  todavía no hay lecciones")
        return

    print(f"  {len(known)} números medidos en results/ y en el temario")
    problems = []
    for path in lecciones:
        found = check(path, known, excepciones) + headline(path, temario, excepciones)
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
