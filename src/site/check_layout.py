"""La maqueta no puede volver a ser la de Sílice.

Kevin miró la primera versión de este curso y dijo que se parecía a sus otras
páginas: el landing, Concentra, Sílice, «se ve y se siente igual». Tenía razón,
y la causa era que el motor se heredó junto con la plantilla: mismo ancho de
prosa (680), mismo ancho de bloques (1180), misma columna de margen (132), 36 de
40 clases compartidas.

Recolorear no arregla eso. Lo que lo arregla es la silueta, y una silueta se
pierde sin querer en cualquier refactor. Este verificador impide que vuelva:

  1. Ninguna de las tres medidas heredadas puede aparecer en el CSS.
  2. Tiene que haber rejilla de dos columnas y un elemento pegajoso, que es
     exactamente lo que ninguno de los otros cuatro sitios tiene.
  3. Las medidas propias tienen que estar declaradas.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_layout.py
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
CSS = PROJECT / "src" / "site" / "templates" / "_base.css"

# Las tres medidas de Sílice. Volver a cualquiera es volver a la misma página.
HEREDADAS = {
    "680px": "el ancho de prosa de Sílice",
    "1180px": "el ancho de bloques de Sílice",
    "132px": "la columna de margen de Sílice, de la que colgaba el kicker",
}

PROPIAS = ("--rail", "--read", "--block")

ESTRUCTURA = [
    (r"grid-template-columns:\s*var\(--rail\)",
     "la rejilla de dos columnas, que es lo que hace que el texto no esté centrado"),
    (r"position:\s*sticky",
     "la barra pegajosa, el primer elemento fijo de todo el portafolio"),
]


def main() -> None:
    if not CSS.exists():
        raise SystemExit(f"No encuentro {CSS}")
    css = io.open(CSS, encoding="utf-8").read()

    # Los comentarios hablan de las medidas heredadas a propósito, para explicar
    # por qué no están. Se quitan antes de buscarlas.
    sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    problemas = []
    for medida, que_es in HEREDADAS.items():
        if medida in sin_comentarios:
            problemas.append(f"«{medida}» ha vuelto al CSS, y es {que_es}")

    for token in PROPIAS:
        if f"{token}:" not in sin_comentarios:
            problemas.append(f"falta la medida propia {token}")

    for patron, que_es in ESTRUCTURA:
        if not re.search(patron, sin_comentarios):
            problemas.append(f"falta {que_es}")

    print(f"  medidas heredadas ausentes   {len(HEREDADAS) - sum(1 for m in HEREDADAS if m in sin_comentarios)}/{len(HEREDADAS)}")
    print(f"  medidas propias presentes    {sum(1 for t in PROPIAS if f'{t}:' in sin_comentarios)}/{len(PROPIAS)}")
    print(f"  piezas de estructura         {sum(1 for p, _ in ESTRUCTURA if re.search(p, sin_comentarios))}/{len(ESTRUCTURA)}")
    print()

    if problemas:
        for problema in problemas:
            print(f"  {problema}")
        raise SystemExit(f"{len(problemas)} problemas de maqueta. No commitear.")
    print("La maqueta sigue siendo la suya, no la heredada.")


if __name__ == "__main__":
    main()
