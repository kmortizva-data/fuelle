"""Recalcula el arco de acentos para el número de módulos que haya, y lo aplica.

El arco va de un cian de instrumento en los datos crudos a una terracota apagada
en la fuga, así que depende de cuántos módulos haya: si el temario crece o se
recorta, los colores intermedios cambian todos.

Hacerlo a mano invitaba a que el temario y results/palette.json se separaran, y
entonces el color de una lección dejaría de significar dónde está en el arco.

Correr:  .venv\\Scripts\\python.exe src\\site\\apply_palette.py
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main() -> None:
    temario_path = PROJECT / "temario.json"
    temario = json.loads(io.open(temario_path, encoding="utf-8").read())
    n = len(temario["modules"])

    print(f"Recalculando el arco para {n} módulos...")
    finished = subprocess.run(
        [sys.executable, str(HERE / "palette.py"), str(n)],
        cwd=PROJECT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if finished.returncode:
        print(finished.stdout)
        raise SystemExit("palette.py falló: algún acento no pasa el contraste.")

    palette = json.loads(io.open(PROJECT / "results" / "palette.json", encoding="utf-8").read())
    accents = palette["accents"]
    if len(accents) != n:
        raise SystemExit(f"La paleta trae {len(accents)} acentos y el temario tiene {n}.")

    changed = 0
    for module, accent in zip(temario["modules"], accents):
        nuevo = {"dark": accent["dark"], "light": accent["light"]}
        if module.get("accent") != nuevo:
            changed += 1
        module["accent"] = nuevo

    io.open(temario_path, "w", encoding="utf-8").write(
        json.dumps(temario, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"  {changed} de {n} acentos actualizados en temario.json")
    print(f"  extremos del arco: {accents[0]['dark']} -> {accents[-1]['dark']}")
    print(f"  contraste mínimo medido: "
          f"{min(min(a['contrast_dark'], a['contrast_light']) for a in accents)}")


if __name__ == "__main__":
    main()
