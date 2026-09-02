"""La puerta de paridad: la gemela inglesa dice exactamente los mismos números.

Una traducción es el sitio más fácil del mundo para que un número se redondee sin
que nadie se entere. Este verificador lo impide comparando las dos ediciones de
cada lección en tres cosas:

  1. Las secciones, una a una y en el mismo orden.
  2. Los bloques de código, literales: el SQL no se traduce.
  3. **Los números**, normalizando solo el formato. En español van 1.516.948 y
     3,42; en inglés 1,516,948 y 3.42. Eso es lo único que puede cambiar.

Escrito para Fuelle sobre la idea del de Sílice, que hacía lo mismo con la
anatomía de aquel curso.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_english.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
LESSONS = PROJECT / "lecciones"

FENCE = re.compile(r"^```(\w*)\s*$", re.M)
SECTION = re.compile(r"^## +(.+)$", re.M)
# Un número puede llevar separadores de millar y decimal, en cualquiera de los
# dos convenios. Se captura entero y se normaliza después.
NUMBER = re.compile(r"\d[\d.,]*\d|\d")


def strip_code(text: str) -> str:
    """Fuera los bloques cercados: el código va literal y no se compara aquí."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def code_blocks(text: str) -> list[tuple[str, str]]:
    """Los bloques cercados con su lenguaje: [(lenguaje, contenido), ...].

    El lenguaje hace falta para saber qué se traduce y qué no. Sin él, la
    comparación solo podía contar bloques, que es lo que hacía antes.
    """
    blocks, current, inside, lang = [], [], False, ""
    for line in text.splitlines():
        if line.startswith("```"):
            if inside:
                blocks.append((lang, "\n".join(current)))
                current = []
            else:
                lang = line[3:].strip()
            inside = not inside
            continue
        if inside:
            current.append(line)
    return blocks


# Los campos de un bloque `reto` que son código y no prosa: si se traducen, el
# reto deja de comprobarse contra la misma respuesta en las dos ediciones.
RETO_LITERAL = ("inicio", "esperado", "solucion")


def reto_code(body: str) -> dict[str, str]:
    campos, actual = {}, None
    for line in body.splitlines():
        head, sep, rest = line.partition(":")
        if sep and head.strip() in ("pregunta", "inicio", "esperado", "pista", "solucion"):
            actual = head.strip()
            campos[actual] = [rest.strip()] if rest.strip() else []
        elif actual:
            campos[actual].append(line.rstrip())
    return {k: "\n".join(v).strip() for k, v in campos.items() if k in RETO_LITERAL}


def fragments(body: str) -> list[str]:
    """Los fragmentos de código de un bloque `anota`, sin sus explicaciones."""
    return [line.split("|")[0].strip() for line in body.splitlines() if "|" in line]


def diagrama_forma(body: str) -> list[tuple[bool, int]]:
    """La forma de un `diagrama`: sus filas, y cuántos campos lleva cada una.

    El texto de un diagrama **sí se traduce**, al contrario que el SQL o una
    salida: es contenido que el lector lee, no código que se ejecuta. Compararlo
    byte a byte dejó las lecciones inglesas del módulo 4 y del 11 enseñando su
    esquema en español, y nadie lo vio porque la puerta daba verde.

    Lo que se compara es la estructura: las mismas filas, cada una con los mismos
    campos, y el asterisco de «esta caja está encendida» en las mismas.
    """
    filas = []
    for line in body.splitlines():
        if not line.strip():
            continue
        filas.append((line.lstrip().startswith("*"), line.count("|")))
    return filas


def canonical(number: str) -> str:
    """1.516.948 y 1,516,948 son el mismo número. 3,42 y 3.42 también.

    Se decide cuál es el separador decimal por el último separador que aparece:
    si le siguen uno o dos dígitos, es el decimal; si le siguen tres, es de
    millares. Con eso los dos convenios caen en la misma cadena.
    """
    body = number.replace(" ", "")
    last = max(body.rfind("."), body.rfind(","))
    if last == -1:
        return body
    tail = body[last + 1:]
    if len(tail) == 3 and body.count(".") + body.count(",") >= 1 and len(body) - last - 1 == 3:
        # Puede ser millares. Si TODOS los grupos miden tres, lo es.
        groups = re.split(r"[.,]", body)
        if all(len(g) == 3 for g in groups[1:]):
            return "".join(groups)
    integer = re.sub(r"[.,]", "", body[:last])
    return f"{integer}.{tail}"


def numbers(text: str) -> Counter:
    return Counter(canonical(m.group()) for m in NUMBER.finditer(strip_code(text)))


def numbers_here(text: str) -> Counter:
    """Los números de un trozo cualquiera, sin quitarle los bloques de código."""
    return Counter(canonical(m.group()) for m in NUMBER.finditer(text))


def sections(text: str) -> list[str]:
    return [m.group(1).strip() for m in SECTION.finditer(text)]


def check(spanish: Path, english: Path) -> list[str]:
    problems = []
    es = spanish.read_text(encoding="utf-8")
    en = english.read_text(encoding="utf-8")

    es_sections, en_sections = sections(es), sections(en)
    if len(es_sections) != len(en_sections):
        problems.append(
            f"{spanish.name}: {len(es_sections)} secciones en español y "
            f"{len(en_sections)} en inglés"
        )

    es_code, en_code = code_blocks(es), code_blocks(en)
    if len(es_code) != len(en_code):
        problems.append(
            f"{spanish.name}: {len(es_code)} bloques de código en español y "
            f"{len(en_code)} en inglés"
        )
    else:
        # El cuerpo de este bucle estaba vacío: comparaba y no decía nada, así
        # que durante seis lecciones la puerta solo contó bloques. Ahora sí
        # compara, y distingue lo que se traduce de lo que va literal.
        for i, ((lang_es, a), (lang_en, b)) in enumerate(zip(es_code, en_code), 1):
            if lang_es != lang_en:
                problems.append(
                    f"{spanish.name}: el bloque {i} es «{lang_es}» en español y "
                    f"«{lang_en}» en inglés")
                continue
            if lang_es == "anota":
                # Se traduce la explicación, nunca el fragmento anotado.
                if fragments(a) != fragments(b):
                    problems.append(
                        f"{spanish.name}: la anotación {i} no anota los mismos "
                        f"fragmentos en las dos ediciones")
            elif lang_es == "diagrama":
                if diagrama_forma(a) != diagrama_forma(b):
                    problems.append(
                        f"{spanish.name}: el diagrama {i} no tiene la misma forma "
                        f"en las dos ediciones")
                elif numbers_here(a) != numbers_here(b):
                    problems.append(
                        f"{spanish.name}: el diagrama {i} no dice los mismos números "
                        f"en las dos ediciones")
            elif lang_es == "reto":
                if reto_code(a) != reto_code(b):
                    problems.append(
                        f"{spanish.name}: el reto {i} no lleva el mismo punto de partida, "
                        f"respuesta esperada o solución en las dos ediciones")
            elif a != b:
                problems.append(
                    f"{spanish.name}: el bloque {i} de «{lang_es}» no es idéntico. "
                    f"El código y las salidas no se traducen")

    es_numbers, en_numbers = numbers(es), numbers(en)
    missing = es_numbers - en_numbers
    extra = en_numbers - es_numbers
    for value, count in sorted(missing.items()):
        problems.append(f"{spanish.name}: «{value}» sale {count} vez más en español")
    for value, count in sorted(extra.items()):
        problems.append(f"{spanish.name}: «{value}» sale {count} vez más en inglés")

    return problems


def main() -> None:
    pairs = []
    for spanish in sorted(LESSONS.glob("m[0-9][0-9]_*.md")):
        english = LESSONS / "en" / spanish.name
        if english.exists():
            pairs.append((spanish, english))

    if not pairs:
        print("  no hay ninguna lección con gemela inglesa todavía")
        return

    problems = []
    for spanish, english in pairs:
        found = check(spanish, english)
        state = "verde" if not found else f"{len(found)} problemas"
        print(f"  {spanish.stem:<24} {state}")
        problems += found

    print()
    if problems:
        for problem in problems:
            print(f"  {problem}")
        raise SystemExit(f"{len(problems)} problemas de paridad. No commitear.")
    print(f"Las {len(pairs)} parejas dicen los mismos números.")


if __name__ == "__main__":
    main()
