"""Lo que se mueve, y lo que pasa cuando no se puede mover. La décima puerta.

El plan del curso prometía este verificador desde el principio y nunca se
construyó. Los nueve que había son otros, así que durante veintidós lecciones
**nadie comprobó ninguna de las tres promesas** que este curso hace sobre su
propio movimiento. Y una de ellas ni siquiera tenía quien la leyera: el campo
`instrumento` está declarado en los 31 módulos de `temario.json` y no lo usaba
ningún script.

Empezó con tres reglas y ya son cinco. Cada una se prueba rompiéndola:

  1. **Estado final sin JavaScript.** Toda pieza interactiva tiene que dejar algo
     legible cuando el JavaScript no llega. La consulta viva imprime su SQL en un
     `<pre>`, la perilla llega con los dos trazos ya dibujados. Quien solo lee, lee.
  2. **`prefers-reduced-motion`.** Lo que se mueve se para si el sistema lo pide.
  3. **Un instrumento por lección**, el que declara `temario.json`. La regla existe
     para que el curso no acabe siendo tres cursos pegados.
  4. **Lo que el temario promete de interacción está.** Una lección declarada
     interactiva tiene que traer con qué interactuar.
  5. **Los datos de cada perilla y del panel llevan su huella en la URL**, o una
     caché vieja dibuja el trazo contra un techo que no es el suyo. Pasó en el
     módulo 24, y desde el 30 se mira en todas las páginas, no solo en las
     lecciones: el panel tiene la suya propia.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_motion.py
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
TEMPLATES = Path(__file__).resolve().parent / "templates"
OUT = PROJECT / "out"
TEMARIO = PROJECT / "temario.json"

# Los tres instrumentos del curso son el grafo del lago, la carátula de la cifra
# y el doble trazo. **Solo el tercero deja rastro en el Markdown**: los otros dos
# los pone la plantilla en todas las páginas.
#
# El primer intento de este verificador contaba también la consulta viva y los
# bloques `diagrama`, y acusó a catorce lecciones correctas. Ninguno de los dos
# es un instrumento: la consulta viva es la capa interactiva, que el temario
# declara aparte en `interactivo`, y un `diagrama` es un esquema de contenido,
# como las capas del lago del módulo 4. El fallo era del verificador.
#
# El panel del módulo 30 es el mismo instrumento: la máquina medida contra el
# gemelo, con un mando que elige el día en vez de una perilla que mueve la física.
BLOQUES_DE_INSTRUMENTO = {"perilla": "doble-trazo", "panel": "doble-trazo"}

# Lo que cuenta como interactivo, para contrastarlo con lo que declara el temario.
BLOQUES_INTERACTIVOS = {"sql-vivo", "reto", "perilla", "panel"}

# Lo que cada pieza interactiva tiene que dejar dibujado sin JavaScript, y en qué
# fichero se comprueba que lo hace.
SIN_JAVASCRIPT = {
    "render_lesson.py": [
        # La consulta viva imprime el SQL dos veces: en un <pre> visible sin JS y
        # en el <textarea> que solo sirve con él.
        ("live-static", "la consulta viva no deja su SQL visible sin JavaScript"),
        # La perilla llega con los dos caminos ya calculados en el servidor.
        ("perilla-referencia", "la perilla no trae su trazo de referencia dibujado"),
        ("perilla-actual", "la perilla no trae dibujada su posición de partida"),
    ],
    # El panel llega con el día de partida entero: las dos curvas, la zona sana,
    # la frase del veredicto y la tira del semestre, todo del servidor.
    "render_panel.py": [
        ("pg-maquina", "el panel no trae dibujada la curva de la máquina"),
        ("pg-gemelo", "el panel no trae dibujada la curva del gemelo"),
        ("pg-frase", "el panel no trae escrita la frase del día de partida"),
        ("pg-barras", "el panel no trae dibujada la tira del semestre"),
    ],
}


def sin_comentarios(js: str) -> str:
    """El JavaScript sin sus comentarios, que es donde vive lo que se comprueba."""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    return re.sub(r"//[^\n]*", " ", js)


def bloques(texto: str) -> list[str]:
    return re.findall(r"^```([a-z-]+)\s*$", texto, re.M)


def instrumentos_de(texto: str) -> list[str]:
    return [BLOQUES_DE_INSTRUMENTO[b] for b in bloques(texto)
            if b in BLOQUES_DE_INSTRUMENTO]


def revisa_lecciones(temario: dict) -> list[str]:
    """Un instrumento por lección, el que promete el temario, y la interacción."""
    problemas = []
    por_numero = {m["number"]: m for m in temario["modules"]}
    rutas = sorted(LESSONS.glob("m[0-9][0-9]_*.md"))
    rutas += sorted((LESSONS / "en").glob("m[0-9][0-9]_*.md"))

    for ruta in rutas:
        nombre = ruta.name + (" (en)" if ruta.parent.name == "en" else "")
        texto = io.open(ruta, encoding="utf-8").read()
        marca = re.search(r"^module:\s*(\d+)", texto, re.M)
        if not marca:
            continue
        modulo = por_numero.get(int(marca.group(1)))
        if modulo is None:
            continue

        # 1. Como mucho un instrumento, y el declarado.
        usados = instrumentos_de(texto)
        if len(usados) > 1:
            problemas.append(f"{nombre}: lleva {len(usados)} instrumentos y la regla es uno")
        declarado = modulo.get("instrumento")
        for usado in set(usados):
            if usado != declarado:
                problemas.append(f"{nombre}: usa «{usado}» y el temario "
                                 f"declara «{declarado}»")

        # 2. Y lo que el temario promete de interacción tiene que estar.
        #
        #    Nadie comprobaba esto: una lección podía declararse interactiva y no
        #    traer nada con lo que interactuar, o traer un reto sin anunciarlo.
        presentes = set(bloques(texto)) & BLOQUES_INTERACTIVOS
        if modulo.get("interactivo") and not presentes:
            problemas.append(f"{nombre}: el temario la declara interactiva y no "
                             f"trae consulta viva, reto ni perilla")
        if ("reto" in presentes) != bool(modulo.get("reto")):
            tiene = "trae" if "reto" in presentes else "no trae"
            promete = "sí" if modulo.get("reto") else "no"
            problemas.append(f"{nombre}: {tiene} bloque de reto y el temario "
                             f"promete reto: {promete}")
    return problemas


def revisa_estado_final() -> list[str]:
    """Que cada pieza interactiva deje algo dibujado sin JavaScript."""
    problemas = []
    for fichero, exigencias in SIN_JAVASCRIPT.items():
        ruta = Path(__file__).resolve().parent / fichero
        texto = io.open(ruta, encoding="utf-8").read()
        for clase, queja in exigencias:
            if clase not in texto:
                problemas.append(f"{fichero}: {queja}")
    return problemas


def revisa_movimiento_reducido() -> list[str]:
    """Que lo que se mueve se pare cuando el sistema lo pide."""
    problemas = []
    css = io.open(TEMPLATES / "_base.css", encoding="utf-8").read()
    if "prefers-reduced-motion" not in css:
        problemas.append("_base.css: no respeta prefers-reduced-motion")

    # Y el JavaScript que anima por su cuenta tiene que mirarlo también: una
    # regla de CSS no alcanza a una transición que un script pone a mano.
    #
    # **Sin los comentarios.** La primera versión buscaba el texto en el fichero
    # entero, y al probarla quitando la comprobación de verdad siguió dando
    # verde: la frase seguía escrita en un comentario de al lado. Un verificador
    # al que le vale un comentario es un falso verde de los del módulo 16.
    for js in sorted(TEMPLATES.glob("*.js")):
        texto = sin_comentarios(io.open(js, encoding="utf-8").read())
        anima = "transition" in texto or "requestAnimationFrame" in texto
        if anima and "prefers-reduced-motion" not in texto:
            problemas.append(f"{js.name}: anima y no mira prefers-reduced-motion")
    return problemas


def revisa_huella_de_las_perillas() -> list[str]:
    """Que los datos de cada perilla lleven su huella en la URL.

    Es la cuarta regla y la más aburrida, y viene de un fallo de verdad. El techo
    del eje va escrito en el HTML y las series las trae el navegador de un JSON
    aparte. Si el JSON se queda en la caché y la página no, el trazo se dibuja
    contra un techo que no es el suyo: en el módulo 24, seis de las veintiuna
    posiciones se salían por arriba del marco y se recortaban.

    Nadie lo habría visto desde aquí. Solo se ve moviendo el mando con una caché
    vieja delante, que es exactamente lo que le pasa a quien vuelve a la página.

    Se miran todas las páginas y no solo las lecciones, porque el panel del
    módulo 30 vive también en la suya, y sus datos cambian cada vez que cambia
    un día del veredicto.
    """
    problemas = []
    for pagina in sorted(OUT.glob("*.html")):
        texto = io.open(pagina, encoding="utf-8").read()
        for atributo in ("data-perilla", "data-panel"):
            for fuente in re.findall(atributo + r'="([^"]+)"', texto):
                if "?v=" not in fuente:
                    problemas.append(
                        f"{pagina.name}: {atributo} apunta a «{fuente}» sin huella. "
                        "Un lector con la caché vieja vería el trazo contra otro techo.")
    return problemas


def main() -> None:
    temario = json.loads(io.open(TEMARIO, encoding="utf-8").read())
    problemas = (revisa_estado_final() + revisa_movimiento_reducido()
                 + revisa_lecciones(temario) + revisa_huella_de_las_perillas())

    con_perilla = sum(1 for ruta in sorted(LESSONS.glob("m[0-9][0-9]_*.md"))
                      if instrumentos_de(io.open(ruta, encoding="utf-8").read()))
    print(f"  {con_perilla} lecciones llevan doble trazo, y ninguna más de uno")
    print(f"  el estado final sin JavaScript y prefers-reduced-motion, comprobados")

    print()
    if problemas:
        for p in problemas:
            print(f"  {p}")
        raise SystemExit(f"{len(problemas)} problemas de movimiento. No commitear.")
    print("Lo que se mueve se puede parar, y lo que no se mueve se lee igual.")


if __name__ == "__main__":
    main()
