"""Construye el sitio del curso: la portada con su índice, y todas las lecciones.

Escrito para Fuelle en vez de heredado de Sílice, porque el de allí lleva dentro
mucho que solo tiene sentido en aquel curso (el bloque de memoria, cifras fijas,
la cuenta de apuntes de origen). Lo que sí se hereda entero es `render_lesson`,
que ya hace el Markdown, las secciones tipadas y los dos idiomas.

Lo propio de aquí es el grafo del lago: bronce, plata, oro y el gemelo unidos por
líneas, con los módulos que levantan cada tramo. Es el instrumento de la portada,
y no es decoración: un pipeline de datos es literalmente un grafo de nodos, y
este dice de dónde a dónde va el curso.

Correr:  .venv\\Scripts\\python.exe src\\site\\build_site.py
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_lesson import (  # noqa: E402
    COURSE_DIR, OUT_DIR, ROOT, TEMPLATES, UI, build_page, build_thread,
    cifra_value, is_written, load_style, load_syllabus, module_subtitle,
    module_title, page_name, render_document, set_language, source_dir,
    suffix, top_link, ui_values, SECTION_STYLES,
)

sys.stdout.reconfigure(encoding="utf-8")

# Las secciones de la portada tienen sus propios kickers. Sin esto caían en el
# de por defecto y las cuatro salian etiquetadas como "Nota", que no clasifica
# nada y es justo lo que el kicker existe para evitar.
COURSE_SECTION_STYLES = {
    "es": {
        "qué es esto": ("is-brief", "El encargo"),
        "por qué un compresor": ("is-bridge", "Por qué"),
        "cómo está hecho": ("is-method", "Método"),
        "los datos": ("is-terms", "Fuente"),
    },
    "en": {
        "what this is": ("is-brief", "The brief"),
        "why a compressor": ("is-bridge", "Why"),
        "how it is made": ("is-method", "Method"),
        "the data": ("is-terms", "Source"),
    },
}

INDEX_UI = {
    "es": {
        "eyebrow": "· ingeniería de datos y gemelos digitales, desde cero",
        "toc_title": "Las treinta y una lecciones",
        "lessons_written": "lecciones escritas",
        "modules": "módulos",
        "parts": "partes",
        "graph_title": "Lo que construye el curso",
    },
    "en": {
        "eyebrow": "· data engineering and digital twins, from scratch",
        "toc_title": "The thirty one lessons",
        "lessons_written": "lessons written",
        "modules": "modules",
        "parts": "parts",
        "graph_title": "What the course builds",
    },
}

# Los tramos del grafo y los módulos que trabajan sobre cada capa. El curso
# camina de izquierda a derecha, así que el grafo también.
#
# Los rangos son explícitos y no derivados de las partes, porque las partes no
# calzan con las capas: los seis módulos de SQL consultan la capa de bronce sin
# ser una capa aparte, y los cuatro de PostgreSQL viven sobre la de oro. La
# primera versión los derivaba de las partes y dejaba diez módulos fuera del
# mapa, con dos tramos solapados. Estos cubren del 1 al 31 sin huecos.
STAGES = [
    ("CRUDO", "RAW", (1, 3)),
    ("BRONCE", "BRONZE", (4, 13)),
    ("PLATA", "SILVER", (14, 16)),
    ("ORO", "GOLD", (17, 22)),
    ("GEMELO", "TWIN", (23, 31)),
]


def build_graph(syllabus: dict, lang: str) -> str:
    """El grafo del lago, en SVG generado, sin imágenes ni librerías.

    Se dibuja con las medidas calculadas aquí para que no dependa de una fuente
    concreta ni de un tamaño de ventana, y para que su estado final se vea sin
    JavaScript, que es la condición de toda pieza visual de este curso.
    """
    box_w, box_h, gap = 148, 46, 34
    width = len(STAGES) * box_w + (len(STAGES) - 1) * gap
    height = 108
    y = 30

    pieces = []
    for i, (es, en, (lo, hi)) in enumerate(STAGES):
        x = i * (box_w + gap)
        label = es if lang == "es" else en

        if i:  # la línea que llega desde el nodo anterior
            x0 = x - gap
            pieces.append(
                f'<path class="edge" d="M {x0} {y + box_h / 2} H {x}" />'
                f'<path class="edge" d="M {x - 7} {y + box_h / 2 - 4} '
                f'l 7 4 l -7 4" />'
            )

        rango = f"{lo}-{hi}" if lo != hi else str(lo)

        pieces.append(
            f'<rect class="node-box" x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="3" />'
            f'<text class="node-label" x="{x + box_w / 2}" y="{y + 27}" '
            f'text-anchor="middle">{html.escape(label)}</text>'
            f'<text class="node-sub" x="{x + box_w / 2}" y="{y + box_h + 18}" '
            f'text-anchor="middle">{html.escape(rango)}</text>'
        )

    return (
        f'<div class="grafo">'
        f'<span class="kicker-inline">{html.escape(INDEX_UI[lang]["graph_title"])}</span>'
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(INDEX_UI[lang]["graph_title"])}">'
        f'{"".join(pieces)}</svg></div>'
    )


def build_toc(syllabus: dict, lang: str) -> str:
    """Cada módulo con su cifra, agrupados por parte y diciendo cuál está escrito."""
    rows = []
    previous = None
    for module in syllabus["modules"]:
        parte = module["parte"]
        if parte != previous:
            titulo = next(p for p in syllabus["partes"] if p["n"] == parte)
            texto = (titulo.get("title_en") or titulo["title"]) if lang == "en" else titulo["title"]
            rows.append(f'<p class="part">{html.escape(texto)}</p>')
            previous = parte

        number = f'<span class="num">{module["number"]:02d}</span>'
        name = (f'<span class="name">{html.escape(module_title(module, lang))}'
                f'<small>{html.escape(module_subtitle(module, lang))}</small></span>')
        accent = f'--accent: {module["accent"]["dark"]}'

        if is_written(module["slug"], lang):
            mark = f'<span class="mark">{html.escape(cifra_value(module, lang))}</span>'
            rows.append(f'<a href="{page_name(module["slug"], lang)}" style="{accent}">'
                        f"{number}{name}{mark}</a>")
        else:
            tag = f'<span class="tag">{html.escape(UI[lang]["pending"])}</span>'
            rows.append(f'<span class="pending">{number}{name}{tag}</span>')
    return "".join(rows)


def build_index(syllabus: dict, written: int, lang: str) -> Path:
    set_language(lang)
    overview = source_dir(lang) / "curso.md"
    if not overview.exists():
        raise SystemExit(f"Falta {overview.relative_to(ROOT)}, que es la portada del curso.")

    body = overview.read_text(encoding="utf-8")
    if body.startswith("---"):
        _, _, body = body.split("---", 2)

    strings = INDEX_UI[lang]
    total = len(syllabus["modules"])
    name = (syllabus.get("course_name_en") or syllabus["course_name"]) \
        if lang == "en" else syllabus["course_name"]
    subtitle = (syllabus.get("course_subtitle_en") or syllabus["course_subtitle"]) \
        if lang == "en" else syllabus["course_subtitle"]

    assay = (f"<span class=\"figure-value\">{written} / {total}</span>"
             f"<span class=\"figure-label\">{strings['lessons_written']}</span>")

    # El acento de la portada es el del primer módulo: el arranque del arco.
    first = syllabus["modules"][0]["accent"]
    page = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    text_values = {
        "{{PAGE_TITLE}}": f"{name} · {subtitle}",
        "{{COURSE_TITLE}}": name,
        "{{EYEBROW}}": strings["eyebrow"],
        "{{SUBTITLE}}": subtitle,
        "{{UI_TOC_TITLE}}": strings["toc_title"],
        "{{ACCENT_LIGHT}}": first["light"],
        "{{ACCENT_DARK}}": first["dark"],
    }
    text_values.update(ui_values(lang))
    link, alternate = top_link("index", lang)
    html_values = {
        "{{STYLE}}": load_style(),
        "{{CONTENT}}": render_document(body, COURSE_SECTION_STYLES[lang], figures=False),
        "{{GRAPH}}": build_graph(syllabus, lang),
        "{{TOC}}": build_toc(syllabus, lang),
        "{{ASSAY}}": assay,
        "{{TOPLINK}}": link,
        "{{ALTERNATE}}": alternate,
    }
    for key, value in text_values.items():
        page = page.replace(key, html.escape(value, quote=True))
    for key, value in html_values.items():
        page = page.replace(key, value)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"index{suffix(lang)}.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


def main() -> None:
    syllabus = load_syllabus()
    total = len(syllabus["modules"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # El JS de las consultas vivas viaja junto a las páginas, no se enlaza al
    # código fuente desde el HTML publicado.
    shutil.copy2(TEMPLATES / "live.js", OUT_DIR / "live.js")

    for lang in ("es", "en"):
        if not (source_dir(lang) / "curso.md").exists():
            print(f"  {lang}: sin portada, saltado")
            continue

        written = 0
        for module in syllabus["modules"]:
            source = source_dir(lang) / f"{module['slug']}.md"
            if source.exists():
                build_page(source, lang)
                written += 1

        index = build_index(syllabus, written, lang)
        print(f"  {lang}  {written}/{total} lecciones  ->  {index.relative_to(ROOT)} "
              f"({index.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
