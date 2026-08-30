"""Los acentos del temario son los que la paleta calculó, y siguen pasando AA.

`palette.py` genera el arco en OKLCH midiendo el contraste, y `apply_palette.py`
lo escribe en `temario.json`. Entre esos dos pasos y el sitio publicado hay sitio
de sobra para que se separen: alguien toca un color a mano, se añade un módulo y
no se recalcula, se cambia un fondo y nadie vuelve a medir.

Esta puerta comprueba tres cosas:

  1. Que hay un acento por módulo, y ninguno repetido.
  2. Que cada uno coincide con lo que `results/palette.json` calculó.
  3. Que todos siguen pasando AA (4,5) sobre los dos fondos, remidiendo aquí en
     vez de fiarse de lo que el JSON dice de sí mismo.

La tercera es la que importa: un color puede estar donde debe y no valer.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_palette.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from palette import BG_DARK, BG_LIGHT, MIN_CONTRAST, contrast  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]


def main() -> None:
    temario = json.loads(io.open(PROJECT / "temario.json", encoding="utf-8").read())
    paleta = json.loads(io.open(PROJECT / "results" / "palette.json", encoding="utf-8").read())
    modulos = temario["modules"]
    accents = paleta["accents"]

    problemas = []

    if len(accents) != len(modulos):
        problemas.append(
            f"la paleta trae {len(accents)} acentos y el temario tiene {len(modulos)} módulos. "
            f"Corre src/site/apply_palette.py")

    vistos = {}
    for i, m in enumerate(modulos):
        acento = m.get("accent")
        if not isinstance(acento, dict) or "dark" not in acento or "light" not in acento:
            problemas.append(f"módulo {m['number']}: el acento no es una pareja clara y oscura")
            continue

        clave = (acento["dark"], acento["light"])
        if clave in vistos:
            problemas.append(f"módulo {m['number']}: repite el acento del módulo {vistos[clave]}")
        vistos[clave] = m["number"]

        if i < len(accents):
            calculado = accents[i]
            for tema, fondo in (("dark", BG_DARK), ("light", BG_LIGHT)):
                if acento[tema] != calculado[tema]:
                    problemas.append(
                        f"módulo {m['number']}: el acento {tema} es {acento[tema]} y la paleta "
                        f"calculó {calculado[tema]}. Corre apply_palette.py")
                # Se remide aquí: que el JSON diga que pasa no es que pase.
                medido = contrast(acento[tema], fondo)
                if medido < MIN_CONTRAST:
                    problemas.append(
                        f"módulo {m['number']}: el acento {tema} {acento[tema]} da {medido:.2f} "
                        f"de contraste, por debajo de {MIN_CONTRAST}")

    series = paleta["fixed"]["series"]
    for tema, s in series.items():
        if s["separation"] < 1.8:
            problemas.append(
                f"las dos series del gemelo en {tema} solo se separan {s['separation']}: "
                f"con el color no basta para distinguirlas")

    print(f"  {len(modulos)} módulos, {len(vistos)} acentos distintos")
    print(f"  contraste mínimo remedido: "
          f"{min(contrast(m['accent'][t], f) for m in modulos if isinstance(m.get('accent'), dict) for t, f in (('dark', BG_DARK), ('light', BG_LIGHT))):.2f}")
    print(f"  separación de las series: "
          f"{ {t: s['separation'] for t, s in series.items()} }")
    print()

    if problemas:
        for p in problemas[:15]:
            print(f"  {p}")
        raise SystemExit(f"{len(problemas)} problemas de paleta. No commitear.")
    print("Los acentos son los calculados y todos pasan AA en los dos temas.")


if __name__ == "__main__":
    main()
