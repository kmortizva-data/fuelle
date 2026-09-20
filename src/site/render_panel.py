"""The twin's panel as HTML: one piece for its own page and for lesson 30.

`src/twin/panel.py` decides everything and writes it to one JSON per language.
This file only draws it, on the server, so the page reads whole without
JavaScript: the day it opens on, with its two curves, its healthy zone, its
marks and its sentence, and the whole semester in a strip underneath. What
`panel.js` adds is choosing another day, and it draws with the same arithmetic
as `camino()` here.

Two consumers, one renderer. `build_panel_page` writes out/panel.html and
out/panel.en.html, and `render_lesson` calls `widget` for a ```panel block.

The chart is an SVG stretched to whatever box it gets (preserveAspectRatio
none), with strokes that do not thicken when stretched (vector-effect). Every
piece of text sits on top in HTML instead: text inside an SVG that shrinks to a
375 px phone ends up four pixels tall.

Run through:  .venv\\Scripts\\python.exe src\\site\\build_site.py
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PANEL_DIR = ROOT / "assets" / "panel"
COURSE_DIR = ROOT / "lecciones"
TEMPLATES = Path(__file__).resolve().parent / "templates"
OUT_DIR = ROOT / "out"

# El módulo cuya cifra enseña la barra de la página: el veredicto.
MODULO_DEL_VEREDICTO = 28
MODULO_DEL_PANEL = 30

UI = {
    "es": {
        "eje_y": "horas cargando, acumuladas",
        "eje_x": "hora del día",
        "maquina": "el compresor, medido",
        "gemelo": "el gemelo, con la máquina sana",
        "zona": "zona sana, hasta el suelo de ruido",
        "hueco": "sin registro",
        "tira": "El semestre entero. Cada barra es un día y su altura el residual más alto "
                "de ese día; la raya discontinua es el umbral de la alarma, y los cuadros "
                "de abajo marcan los días con parte de avería.",
        "cursor": "elige el día",
        "anterior": "‹ anterior",
        "siguiente": "siguiente ›",
        "atajos": "días que cuentan la historia",
        "sin_js": "Sin JavaScript se ve el día de partida; con él, cualquiera de los "
                  "{n} días.",
        "meses": ["feb", "mar", "abr", "may", "jun", "jul", "ago"],
        "marzo": "marzo, sin parte",
        "horas": "h",
        # La página propia.
        "titulo_pagina": "El panel del gemelo · Fuelle",
        "descripcion": "El semestre de un compresor del Metro de Oporto, día a día: lo "
                       "que trabajó contra lo que habría trabajado sano, y el veredicto "
                       "de cada día.",
        "ceja": "el panel del gemelo",
        "id": "panel",
        "id_texto": "{n} días, del 1 de febrero al 1 de septiembre de 2020",
        "h1": "El semestre del compresor, día a día",
        "entradilla": "Cada día, lo que trabajó el compresor de verdad contra lo que habría "
                      "trabajado sano. Cuando las dos líneas se separan, algo está gastando "
                      "el aire que no debería.",
        "curso": "el curso",
        "folio": "el folio",
        "como": "cómo se hizo",
        "cambio": "English",
        "progreso": "el semestre entero, sin servidor",
    },
    "en": {
        "eje_y": "hours loaded, cumulative",
        "eje_x": "time of day",
        "maquina": "the compressor, measured",
        "gemelo": "the twin, machine healthy",
        "zona": "healthy zone, up to the noise floor",
        "hueco": "no record",
        "tira": "The whole semester. Each bar is a day and its height the day's highest "
                "residual; the dashed line is the alarm threshold, and the squares "
                "underneath mark the days with a failure report.",
        "cursor": "choose the day",
        "anterior": "‹ previous",
        "siguiente": "next ›",
        "atajos": "days that tell the story",
        "sin_js": "Without JavaScript you see the starting day; with it, any of the "
                  "{n} days.",
        "meses": ["Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
        "marzo": "March, no report",
        "horas": "h",
        "titulo_pagina": "The twin's panel · Bellows",
        "descripcion": "The semester of a Porto Metro compressor, day by day: how long it "
                       "worked against how long it would have worked healthy, and each "
                       "day's verdict.",
        "ceja": "the twin's panel",
        "id": "panel",
        "id_texto": "{n} days, from 1 February to 1 September 2020",
        "h1": "The compressor's semester, day by day",
        "entradilla": "Each day, how long the compressor actually worked against how long "
                      "it would have worked healthy. When the two lines part, something "
                      "is drawing air it should not.",
        "curso": "the course",
        "folio": "the verdict",
        "como": "how it was made",
        "cambio": "Español",
        "progreso": "the whole semester, no server",
    },
}

# Las secciones de la página propia, con su etiqueta. Salen de lecciones/panel.md,
# que pasa por las mismas puertas de escritura que las lecciones.
SECCIONES = {
    "es": {"cómo se lee": ("is-method", "Lectura"),
           "de dónde sale": ("is-terms", "Fuente")},
    "en": {"how to read it": ("is-method", "Reading"),
           "where it comes from": ("is-terms", "Source")},
}

# Los días de la tira donde empieza cada mes, contados desde el 1 de febrero.
# Septiembre no lleva etiqueta: es un solo día, el último de la tira, y su
# etiqueta se salía por el borde derecho en un móvil.
PRIMERO_DE_MES = [0, 29, 60, 90, 121, 151, 182]


def datos(lang: str) -> dict:
    fuente = PANEL_DIR / f"semestre.{lang}.json"
    if not fuente.exists():
        raise SystemExit(f"Falta {fuente.relative_to(ROOT)}. Corre src/twin/panel.py.")
    return json.loads(fuente.read_text(encoding="utf-8"))


def huella(lang: str) -> str:
    """La huella del contenido, que viaja en la URL: la quinta regla de check_motion."""
    return hashlib.sha256((PANEL_DIR / f"semestre.{lang}.json").read_bytes()).hexdigest()[:8]


def camino(tramos: list[int], paso: int, techo: int) -> str:
    """La curva acumulada como camino de SVG. La misma cuenta que `camino` en panel.js."""
    d, total = f"M0 {techo}", 0
    for k, t in enumerate(tramos, 1):
        total += t
        d += f" L{k * paso} {techo - total}"
    return d


def pct(x: float, total: float) -> str:
    return f"{100 * x / total:.3f}%"


def huecos(dia: dict, puntos: int) -> str:
    return "".join(
        f'<span class="pg-hueco" style="left:{pct(a, puntos)};width:{pct(b - a, puntos)}">'
        f"</span>" for a, b in dia["huecos"])


def marcas(dia: dict, puntos: int) -> str:
    """Las rayas primero y las etiquetas después, para que ninguna raya tache una
    etiqueta: el 15 de julio tiene tres marcas en cinco horas, y la raya de la
    alarma cruzaba por encima de la etiqueta del parte."""
    rayas, etiquetas = [], []
    for m in dia["marcas"]:
        # La etiqueta sale hacia la derecha de su raya, salvo en el último tercio
        # del día, donde se saldría del gráfico: ahí se escribe hacia la izquierda.
        lado = "izq" if m["x"] / puntos > 0.68 else "der"
        rayas.append(f'<span class="pg-raya" data-tipo="{m["tipo"]}" '
                     f'style="left:{pct(m["x"], puntos)}"></span>')
        etiquetas.append(
            f'<span class="pg-marca" data-tipo="{m["tipo"]}" data-fila="{m["fila"]}" '
            f'data-lado="{lado}" style="left:{pct(m["x"], puntos)}">'
            f'{html.escape(m["t"])}</span>')
    return "".join(rayas + etiquetas)


def tira(j: dict, lang: str, elegido: int) -> str:
    """El semestre en una tira de barras, dibujado entero en el servidor.

    Un día por unidad de ancho, así que el día `i` ocupa de `i` a `i + 1` y su
    centro cae en `i + 0,5`: es la misma posición que le da el mando, que tiene
    el pulgar de dos píxeles para que no desplace nada.
    """
    n = len(j["dias"])
    techo = j["techo_residual"]
    alto = lambda v: max(0.0, min(v, techo)) / techo * 92  # noqa: E731
    barras, partes = [], []
    for k, d in enumerate(j["dias"]):
        elegida = " pg-b-elegido" if k == elegido else ""
        if d["pico"] is None:
            barras.append(f'<rect class="pg-b-sin{elegida}" x="{k + 0.3:.2f}" y="93" '
                          f'width="0.4" height="3"/>')
        else:
            h = max(alto(d["pico"]), 0.8)
            cls = "pg-b-alta" if d["pico"] > j["umbral"] else "pg-b"
            barras.append(f'<rect class="{cls}{elegida}" x="{k + 0.18:.2f}" '
                          f'y="{96 - h:.2f}" width="0.64" height="{h:.2f}"/>')
        if d["clase"] in ("acierto", "escapa"):
            partes.append(f'<rect class="pg-t-parte" x="{k + 0.1:.2f}" y="100" '
                          f'width="0.8" height="8"/>')
    marzo = [k for k, d in enumerate(j["dias"]) if d["clase"].startswith("marzo")]
    umbral_y = 96 - alto(j["umbral"])
    suelo_y = 96 - alto(j["suelo"])
    return (
        f'<svg class="pg-tira-svg" viewBox="0 0 {n} 110" preserveAspectRatio="none" '
        f'aria-hidden="true">'
        f'<path class="pg-t-suelo" d="M0 {suelo_y:.2f} H{n}" '
        f'vector-effect="non-scaling-stroke"/>'
        f'<g class="pg-barras">{"".join(barras)}</g>'
        f'<g>{"".join(partes)}</g>'
        + (f'<path class="pg-t-marzo" d="M{marzo[0] + 0.1} 104 H{marzo[-1] + 0.9}" '
           f'vector-effect="non-scaling-stroke"/>' if marzo else "")
        + f'<path class="pg-t-umbral" d="M0 {umbral_y:.2f} H{n}" '
        f'vector-effect="non-scaling-stroke"/>'
        f'<path class="pg-t-cursor" d="M{elegido + 0.5} 0 V110" '
        f'vector-effect="non-scaling-stroke"/>'
        f"</svg>"
    )


def widget(lang: str, prefijo: str = "../", enlazable: bool = False) -> str:
    """El panel entero, ya dibujado en el día de partida.

    `enlazable` pone el día en la URL al moverse (panel.html#2020-04-18), que
    tiene sentido en la página propia y no dentro de una lección.
    """
    j = datos(lang)
    ui = UI[lang]
    i = j["inicial"]
    dia = j["dias"][i]
    paso, techo, puntos = j["minutos_por_punto"], j["techo_min"], j["puntos"]
    ancho = puntos * paso
    fuente = f"{prefijo}assets/panel/semestre.{lang}.json?v={huella(lang)}"
    n = len(j["dias"])

    rejilla = " ".join(f"M0 {techo - v} H{ancho} M{v} 0 V{techo}" for v in (360, 720, 1080))
    ticks_y = "".join(f'<span class="pg-ty" style="bottom:{pct(h * 60, techo)}">'
                      f'{h} {ui["horas"]}</span>' for h in (0, 6, 12, 18, 24))
    ticks_x = "".join(f'<span class="pg-tx" style="left:{pct(h * 60, ancho)}">'
                      f"{h:02d}:00</span>" for h in (0, 6, 12, 18, 24))
    leyenda = "".join(
        f'<li class="pg-k-{k}"><i></i>{html.escape(ui[k if k != "sin_registro" else "hueco"])}'
        f' <b data-k="{k}">{html.escape(dia["leyenda"][k])}</b></li>'
        for k in ("maquina", "gemelo", "zona", "sin_registro"))
    meses = "".join(f'<span class="pg-mes" style="left:{pct(k, n)}">{m}</span>'
                    for k, m in zip(PRIMERO_DE_MES, ui["meses"]))
    atajos = "".join(
        f'<button type="button" class="pg-atajo" data-i="{a["i"]}" '
        f'aria-pressed="{"true" if a["i"] == i else "false"}" disabled>'
        f'{html.escape(a["t"])}</button>' for a in j["atajos"])

    return (
        f'<figure class="pg" data-panel="{html.escape(fuente)}"'
        f'{" data-enlazable" if enlazable else ""}>'
        f'<div class="pg-cabeza">'
        f'<output class="pg-fecha">{html.escape(dia["fecha"])}</output>'
        f'<span class="pg-clase" data-clase="{dia["clase"]}">'
        f'{html.escape(dia["etiqueta"])}</span></div>'

        f'<div class="pg-grafico">'
        f'<span class="pg-eje-y">{html.escape(ui["eje_y"])}</span>'
        f'<div class="pg-lienzo">'
        f'<div class="pg-huecos">{huecos(dia, puntos)}</div>'
        f'<svg class="pg-svg" viewBox="0 0 {ancho} {techo}" preserveAspectRatio="none" '
        f'aria-hidden="true">'
        f'<path class="pg-rejilla" d="{rejilla}" vector-effect="non-scaling-stroke"/>'
        f'<path class="pg-zona" d="{camino(dia["zona"], paso, techo)} L{ancho} {techo} Z" '
        f'vector-effect="non-scaling-stroke"/>'
        f'<path class="pg-gemelo" d="{camino(dia["gemelo"], paso, techo)}" '
        f'vector-effect="non-scaling-stroke"/>'
        f'<path class="pg-maquina" d="{camino(dia["maquina"], paso, techo)}" '
        f'vector-effect="non-scaling-stroke"/>'
        f"</svg>"
        f'<div class="pg-marcas">{marcas(dia, puntos)}</div>'
        f"{ticks_y}{ticks_x}"
        f"</div>"
        f'<span class="pg-eje-x">{html.escape(ui["eje_x"])}</span>'
        f"</div>"

        f'<ul class="pg-leyenda">{leyenda}</ul>'
        f'<p class="pg-frase" aria-live="polite">{html.escape(dia["frase"])}</p>'

        f'<div class="pg-mando">'
        f'<p class="pg-tira-nota">{html.escape(ui["tira"])}</p>'
        f'<div class="pg-tira">{tira(j, lang, i)}'
        f'<input class="pg-cursor" type="range" min="0" max="{n - 1}" value="{i}" '
        f'step="1" aria-label="{html.escape(ui["cursor"])}" '
        f'aria-valuetext="{html.escape(dia["fecha"] + ", " + dia["etiqueta"])}" disabled>'
        f"</div>"
        f'<div class="pg-meses">{meses}</div>'
        f'<p class="pg-sinjs">{html.escape(ui["sin_js"].format(n=n))}</p>'
        f'<div class="pg-botones">'
        f'<button type="button" class="pg-paso" data-paso="-1" disabled>'
        f'{html.escape(ui["anterior"])}</button>'
        f'<button type="button" class="pg-paso" data-paso="1" disabled>'
        f'{html.escape(ui["siguiente"])}</button>'
        f'<span class="pg-atajos-titulo">{html.escape(ui["atajos"])}</span>'
        f"{atajos}</div>"
        f"</div>"
        f"</figure>"
    )


def build_panel_page(lang: str) -> Path:
    """La página propia del panel: la puerta para quien no va a leer 31 módulos."""
    # Importado aquí para que render_lesson pueda importar este fichero sin ciclo.
    from render_lesson import (  # noqa: E402
        build_rail, cifra_label, cifra_value, is_written, load_style, load_syllabus,
        page_name, render_document, set_language, suffix, ui_values,
    )

    set_language(lang)
    syllabus = load_syllabus()
    ui = UI[lang]
    veredicto = next(m for m in syllabus["modules"] if m["number"] == MODULO_DEL_VEREDICTO)
    este = next(m for m in syllabus["modules"] if m["number"] == MODULO_DEL_PANEL)
    n = len(datos(lang)["dias"])

    fuente = (COURSE_DIR if lang == "es" else COURSE_DIR / "en") / "panel.md"
    if not fuente.exists():
        raise SystemExit(f"Falta {fuente.relative_to(ROOT)}, el texto de la página del panel.")
    cuerpo = fuente.read_text(encoding="utf-8")

    enlaces = [f'<a href="index{suffix(lang)}.html">{html.escape(ui["curso"])}</a>',
               f'<a href="folio{suffix(lang)}.html">{html.escape(ui["folio"])}</a>']
    if is_written(este["slug"], lang):
        enlaces.append(f'<a href="{page_name(este["slug"], lang)}">'
                       f'{html.escape(ui["como"])}</a>')
    otro = "en" if lang == "es" else "es"
    enlaces.append(f'<a class="portfolio-link" href="panel{suffix(otro)}.html" '
                   f'hreflang="{otro}" rel="alternate">{html.escape(ui["cambio"])}</a>')
    alterna = f'<link rel="alternate" hreflang="{otro}" href="panel{suffix(otro)}.html">'

    pagina = (TEMPLATES / "panel.html").read_text(encoding="utf-8")
    texto = {
        "{{PAGE_TITLE}}": ui["titulo_pagina"],
        "{{DESCRIPTION}}": ui["descripcion"],
        "{{EYEBROW}}": ui["ceja"],
        "{{PANEL_ID}}": ui["id"],
        "{{PANEL_ID_TEXT}}": ui["id_texto"].format(n=n),
        "{{TITLE}}": ui["h1"],
        "{{SUBTITLE}}": ui["entradilla"],
        "{{CIFRA_VALUE}}": cifra_value(veredicto, lang),
        "{{CIFRA_LABEL}}": cifra_label(veredicto, lang),
        "{{PROGRESS_TEXT}}": ui["progreso"],
        "{{ACCENT_LIGHT}}": este["accent"]["light"],
        "{{ACCENT_DARK}}": este["accent"]["dark"],
    }
    texto.update(ui_values(lang))
    marcado = {
        "{{STYLE}}": load_style(),
        "{{RAIL}}": build_rail(MODULO_DEL_PANEL, lang),
        "{{NAV}}": "".join(enlaces),
        "{{ALTERNATE}}": alterna,
        "{{WIDGET}}": widget(lang, "../", enlazable=True),
        "{{CONTENT}}": render_document(cuerpo, SECCIONES[lang], figures=False),
    }
    for clave, valor in texto.items():
        pagina = pagina.replace(clave, html.escape(valor, quote=True))
    for clave, valor in marcado.items():
        pagina = pagina.replace(clave, valor)
    # Ninguna llave puede quedar sin rellenar: sería texto de plantilla publicado.
    if "{{" in pagina:
        resto = pagina[pagina.index("{{"):][:40]
        raise SystemExit(f"La página del panel ({lang}) deja una llave sin rellenar: {resto}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    destino = OUT_DIR / f"panel{suffix(lang)}.html"
    destino.write_text(pagina, encoding="utf-8")
    return destino
