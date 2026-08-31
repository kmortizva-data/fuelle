"""Render a lesson (Markdown source) into a standalone HTML page, in Spanish or English.

A lesson file carries almost no metadata: only which module it is. Everything else, the
title, the subtitle, the accent, the headline figure, the source notes, comes from
2_Curso/temario.json, which was written before the first lesson existed. That is the whole
point of the reorganisation: the plan is the single source of truth and a lesson cannot
quietly disagree with it.

Two editions. The Spanish lesson lives in 2_Curso/mNN_slug.md and renders to
out/mNN_slug.html; its English twin lives in 2_Curso/en/mNN_slug.md and renders to
out/mNN_slug.en.html, next to it, so every relative path (figures, stylesheet) is the same
for both. A page links its twin when the twin exists; until then the Spanish page offers
the English summary on the portfolio instead, which is an honest door rather than a
switch to nowhere. check_english.py keeps the twins in step (same sections, same figures,
same numbers).

Usage:
    python src/site/render_lesson.py 2_Curso/m01_*.md [more.md ...]
    python src/site/render_lesson.py 2_Curso/en/m01_*.md
    python src/site/render_lesson.py --all
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
COURSE_DIR = ROOT / "lecciones"

# A lesson file is m<NN>_<slug>.md. The pattern is this strict because Windows
# matches globs case-insensitively, so a loose "m*.md" also picked up MANUAL.md and
# reported the manual for quoting the very phrases it bans.
LESSON_GLOB = "m[0-9][0-9]_*.md"

FIGURES_DIR = ROOT / "figuras"
OUT_DIR = ROOT / "out"
RESULTS_DIR = ROOT / "results"
TEMPLATES = Path(__file__).resolve().parent / "templates"

LANGS = ("es", "en")


def source_dir(lang: str) -> Path:
    """Where a language's sources live: Spanish at the course root, English in en/."""
    return COURSE_DIR if lang == "es" else COURSE_DIR / "en"


def suffix(lang: str) -> str:
    """The output file suffix: mNN_slug.html for Spanish, mNN_slug.en.html for English."""
    return "" if lang == "es" else ".en"


def other(lang: str) -> str:
    return "en" if lang == "es" else "es"


# Section heading -> (css modifier, kicker), per language. The kicker classifies the
# block instead of decorating it: emoji headers were one more thing that made a page read
# as generated. The English headings are the ones check_english.py requires.
SECTION_STYLES = {
    "es": {
        "en 30 segundos": ("is-brief", "Resumen"),
        "qué resuelve este módulo": ("", "Contexto"),
        "antes de la teoría: un ejemplo de juguete": ("is-toy", "A mano"),
        "el arco del proyecto": ("is-toy", "Recorrido"),
        "glosario": ("is-terms", "Términos"),
        "paso a paso": ("is-method", "Método"),
        "el código, por partes": ("is-code", "Código"),
        "el resultado, medido": ("is-result", "Resultado"),
        "ojo": ("is-warning", "Trampas"),
        "hazlo tú": ("is-live", "Hazlo tú"),
        "puente metalúrgico": ("is-bridge", "Analogía"),
        "repaso": ("is-review", "Repaso"),
    },
    "en": {
        "in 30 seconds": ("is-brief", "Summary"),
        "what this module solves": ("", "Context"),
        "before the theory: a toy example": ("is-toy", "By hand"),
        "the arc of the project": ("is-toy", "The path"),
        "glossary": ("is-terms", "Terms"),
        "step by step": ("is-method", "Method"),
        "the code, in parts": ("is-code", "Code"),
        "the result, measured": ("is-result", "Result"),
        "watch out": ("is-warning", "Traps"),
        "do it yourself": ("is-live", "Your turn"),
        "metallurgical bridge": ("is-bridge", "Analogy"),
        "review": ("is-review", "Review"),
    },
}
DEFAULT_STYLE = {"es": ("", "Nota"), "en": ("", "Note")}
REVIEW_HEADINGS = {"repaso", "review"}
GLOSSARY_HEADINGS = {"glosario", "glossary"}

# Every piece of interface text, per language. The lessons themselves are written in
# each language; this is only the chrome around them.
UI = {
    "es": {
        "course_name": "Fuelle",
        "page_title": "{title} · Fuelle, módulo {n}",
        "prints": "sale",
        "line_by_line": "línea por línea, {n} {label}",
        "entry": "entrada", "entries": "entradas",
        "terms": "{n} términos, en palabras simples",
        "module": "Módulo", "of": "de",
        "prev": "Anterior", "next": "Siguiente",
        "lessons": "lecciones", "notes": "apuntes de origen",
        "figures": "figuras", "scripts": "scripts",
        "thread": "El arco del proyecto",
        "generated": "generado el", "source": "fuente",
        "source_note": "MetroPT-3, del compresor de un tren del Metro de Oporto (CC BY 4.0)",
        "run": "correr", "challenge_run": "comprobar",
        "idle": "el motor se descarga al pulsar",
        "live_label": "consulta viva", "challenge_label": "reto",
        "hint": "una pista", "solution": "ver la solución",
        "pending": "pendiente",
        "switch": "English",
        "rail": "el lago", "part": "parte:", "written": "lecciones escritas",
        "modules_word": "módulos", "parts_word": "partes", "course": "el curso",
        "toc_kicker": "Temario",
        "portfolio": "English summary on the portfolio ↗",
    },
    "en": {
        "course_name": "Bellows",
        "page_title": "{title} · Bellows, module {n}",
        "prints": "prints",
        "line_by_line": "line by line, {n} {label}",
        "entry": "entry", "entries": "entries",
        "terms": "{n} terms, in plain words",
        "module": "Module", "of": "of",
        "prev": "Previous", "next": "Next",
        "lessons": "lessons", "notes": "source notes",
        "figures": "figures", "scripts": "scripts",
        "thread": "The arc of the project",
        "generated": "generated on", "source": "source",
        "source_note": "MetroPT-3, from a Porto Metro train compressor (CC BY 4.0)",
        "run": "run", "challenge_run": "check",
        "idle": "the engine downloads when you press",
        "live_label": "live query", "challenge_label": "challenge",
        "hint": "a hint", "solution": "see the solution",
        "pending": "pending",
        "switch": "Español",
        "rail": "the lake", "part": "part:", "written": "lessons written",
        "modules_word": "modules", "parts_word": "parts", "course": "the course",
        "toc_kicker": "Syllabus",
        "portfolio": "Resumen en el portafolio ↗",
    },
}
SOURCE_NOTE = UI["es"]["source_note"]

# The language being rendered. Set once per page, read by the block renderers, so the
# Markdown subset does not have to thread a parameter through every function.
_lang = "es"


def set_language(lang: str) -> None:
    global _lang
    _lang = lang


def ui(key: str) -> str:
    return UI[_lang][key]


def module_title(module: dict, lang: str) -> str:
    return module.get("title_en") or module["title"] if lang == "en" else module["title"]


def module_subtitle(module: dict, lang: str) -> str:
    return (module.get("subtitle_en") or module["subtitle"]) if lang == "en" else module["subtitle"]


def cifra_value(module: dict, lang: str) -> str:
    figure = module["cifra"]
    return (figure.get("value_en") or figure["value"]) if lang == "en" else figure["value"]


def cifra_label(module: dict, lang: str) -> str:
    figure = module["cifra"]
    return (figure.get("label_en") or figure["label"]) if lang == "en" else figure["label"]


def load_style() -> str:
    """The shared stylesheet, inlined so every page stays self-contained offline."""
    return (TEMPLATES / "_base.css").read_text(encoding="utf-8")


def load_syllabus() -> dict:
    return json.loads((ROOT / "temario.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- inline

def inline(text: str) -> str:
    """Convert the inline Markdown subset: code, bold, italics, links."""
    placeholders: list[str] = []

    def stash(markup: str) -> str:
        placeholders.append(markup)
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)
    return text


# --------------------------------------------------------------------------- blocks

def render_table(rows: list[str]) -> str:
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
    header, body = cells[0], cells[2:]  # cells[1] is the |---|---| separator
    head_html = "".join(f"<th>{inline(c)}</th>" for c in header)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body
    )
    return (
        f'<div class="table-wrap"><table><thead><tr>{head_html}</tr></thead>'
        f"<tbody>{body_html}</tbody></table></div>"
    )


def render_blocks(lines: list[str]) -> str:
    """Render the Markdown subset: paragraphs, lists, tables, code fences, quotes."""
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        heading = re.match(r"^(#{3,4})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            out.append(f'<h{level} class="sub">{inline(heading.group(2))}</h{level}>')
            index += 1
            continue

        if line.startswith("```"):
            language = line[3:].strip()
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1  # closing fence
            body = html.escape("\n".join(code))
            # A `salida` block is what the code prints, not code to run: it gets its own
            # look so the reader never confuses input with output.
            if language == "salida":
                out.append(f'<div class="output"><span class="output-tag">{ui("prints")}</span>'
                           f"<pre><code>{body}</code></pre></div>")
            # An `anota` block explains the code line by line, for a reader who has not
            # programmed before. Each line is "fragmento | qué hace".
            elif language == "anota":
                rows = []
                for entry in code:
                    if "|" not in entry:
                        continue
                    fragment, _, meaning = entry.partition("|")
                    rows.append(
                        f"<dt><code>{html.escape(fragment.strip())}</code></dt>"
                        f"<dd>{inline(meaning.strip())}</dd>"
                    )
                label = ui("entry") if len(rows) == 1 else ui("entries")
                out.append(fold('<dl class="annot">' + "".join(rows) + "</dl>",
                                ui("line_by_line").format(n=len(rows), label=label)))

            # Un bloque `sql-vivo` es una consulta que el lector puede editar y
            # correr de verdad, contra los datos reales, dentro de su navegador.
            # El SQL se imprime siempre, asi que sin JavaScript la leccion se lee
            # entera; lo que anade el JS es poder tocarla.
            elif language == "sql-vivo":
                out.append(live_block(body))
            # Un bloque `reto` es lo mismo mas un enunciado y una respuesta
            # esperada. La pagina compara EL RESULTADO, nunca el texto.
            elif language == "reto":
                out.append(challenge_block(code))
            # Un bloque `diagrama` es un esquema conceptual, no una figura de
            # datos: las capas del lago, el recorrido de un fichero. Matplotlib
            # dibuja mal estas cosas y ademas obligaria a generar dos versiones,
            # una por tema. Esto se genera con los tokens de la propia pagina,
            # asi que responde al tema solo, se reordena en movil, y su texto es
            # texto de verdad que se puede copiar y leer con un lector.
            elif language == "diagrama":
                out.append(diagram_block(code))
            else:
                css_class = f' class="language-{language}"' if language else ""
                out.append(f"<pre><code{css_class}>{body}</code></pre>")
            continue

        if line.startswith("|"):
            table: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                table.append(lines[index])
                index += 1
            out.append(render_table(table) if len(table) >= 2 else "")
            continue

        if line.startswith("> "):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("> "):
                quote_lines.append(lines[index][2:])
                index += 1
            out.append(f"<blockquote>{inline(' '.join(quote_lines))}</blockquote>")
            continue

        bullet = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if bullet:
            ordered = bullet.group(2)[0].isdigit()
            items: list[str] = []
            while index < len(lines):
                current = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[index])
                if not current:
                    # a plain indented line continues the previous bullet
                    if items and lines[index].startswith("  ") and lines[index].strip():
                        items[-1] += " " + inline(lines[index].strip())
                        index += 1
                        continue
                    break
                items.append(inline(current.group(3)))
                index += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{item}</li>" for item in items) + f"</{tag}>")
            continue

        paragraph: list[str] = []
        while index < len(lines) and lines[index].strip() and not re.match(
            r"^(#{3,4}\s|```|\||> |\s*([-*]|\d+\.)\s)", lines[index]
        ):
            paragraph.append(lines[index].strip())
            index += 1
        out.append(f"<p>{inline(' '.join(paragraph))}</p>")

    return "".join(out)


# --------------------------------------------------------- que muestra se baja

# Cada modulo declara en `temario.json` que muestra necesita, porque no todos
# necesitan lo mismo y la mas cara pesa cuarenta veces mas que la mas barata.
# El modulo 13 necesita la hora exacta, que cuesta 5,16 MB si se lleva el lago
# entero, asi que se lleva un solo dia. Los demas no necesitan la hora.
MUESTRA_POR_DEFECTO = "sin_timestamp_ligera"


def tables_for(module: dict) -> str:
    """`vista=fichero.parquet`, separadas por comas, para que lo lea live.js.

    Se emite siempre, tambien en los modulos sin consulta viva: no cuesta nada y
    evita que anadir un bloque `sql-vivo` a una leccion exija tocar la plantilla.
    """
    pares = [f"telemetria={module.get('muestra', MUESTRA_POR_DEFECTO)}.parquet"]
    for extra in module.get("tablas_extra", []):
        pares.append(f"{extra}={extra}.parquet")
    return ",".join(pares)


# ------------------------------------------------------------------- diagramas

def diagram_block(lines: list[str]) -> str:
    """Un esquema de cajas encadenadas, generado con los tokens de la pagina.

    La gramatica es una linea por caja:

        NOMBRE | que es | nota al pie

    Un asterisco delante del nombre enciende la caja, que es como una leccion
    marca el tramo que esta construyendo. Los dos ultimos campos son opcionales.

    Se genera HTML y no SVG a proposito. Un SVG tendria que traer sus colores
    dentro, o dos versiones, y no se reordenaria en un movil. Con cajas de HTML
    el tema y el ancho los resuelve el CSS, que es donde viven esas decisiones.
    """
    nodes = []
    for entry in lines:
        raw = entry.strip()
        if not raw:
            continue
        lit = raw.startswith("*")
        name, _, rest = raw.lstrip("*").strip().partition("|")
        what, _, note = rest.partition("|")
        inner = [f'<span class="node-name">{inline(name.strip())}</span>']
        if what.strip():
            inner.append(f'<span class="node-what">{inline(what.strip())}</span>')
        if note.strip():
            inner.append(f'<span class="node-note">{inline(note.strip())}</span>')
        cls = "node lit" if lit else "node"
        nodes.append(f'<li class="{cls}">' + "".join(inner) + "</li>")
    return f'<figure class="diagram"><ol class="chain">{"".join(nodes)}</ol></figure>'


# --------------------------------------------------------------- consulta viva

def _editor(sql: str, label: str, run_label: str, extra: str = "", data: str = "") -> str:
    """El armazon compartido por la consulta viva y el reto.

    El SQL va DOS veces a proposito: en un <pre> que se ve cuando no hay
    JavaScript, y en el <textarea> que se ve cuando si lo hay. Asi la leccion
    nunca depende del motor para poder leerse.
    """
    return (
        f'<div class="live{extra}"{data}>'
        f'<div class="live-head"><span>{html.escape(label)}</span>'
        f'<span class="live-status">{html.escape(ui("idle"))}</span></div>'
        f'<pre class="live-static"><code>{sql}</code></pre>'
        f'<textarea class="live-editor" spellcheck="false" '
        f'aria-label="{html.escape(label)}">{sql}</textarea>'
        f'<div class="live-bar"><button type="button" class="live-run">'
        f'{html.escape(run_label)}</button></div>'
        f'<div class="live-out"></div>'
    )


def live_block(escaped_sql: str) -> str:
    return _editor(escaped_sql, ui("live_label"), ui("run")) + "</div>"


def challenge_block(lines: list[str]) -> str:
    """Un reto: enunciado, punto de partida, pista y solucion, todo plegado.

    Campos, uno por linea: `pregunta:`, `inicio:`, `esperado:`, `pista:`,
    `solucion:`. `esperado` nombra una clave de results/retos.json, que escriben
    los scripts al resolver el reto; ninguna respuesta se teclea a mano aqui.
    """
    fields: dict[str, list[str]] = {}
    current = None
    for line in lines:
        head, sep, rest = line.partition(":")
        if sep and head.strip() in ("pregunta", "inicio", "esperado", "pista", "solucion"):
            current = head.strip()
            fields[current] = [rest.strip()] if rest.strip() else []
        elif current:
            fields[current].append(line.rstrip())

    def joined(key: str) -> str:
        return "\n".join(fields.get(key, [])).strip()

    expected_key = joined("esperado")
    payload = ""
    if expected_key:
        answers = json.loads((RESULTS_DIR / "retos.json").read_text(encoding="utf-8"))
        if expected_key not in answers:
            raise SystemExit(
                f"El reto pide la respuesta «{expected_key}» y no está en "
                f"results/retos.json. Resuélvelo con su script antes de publicarlo."
            )
        payload = (" data-expected='"
                   + html.escape(json.dumps(answers[expected_key]["rows"]), quote=True)
                   + "'")

    ask = f'<p class="reto-ask">{inline(joined("pregunta"))}</p>'
    start = html.escape(joined("inicio"))
    body = _editor(start, ui("challenge_label"), ui("challenge_run"), " reto", payload)
    tail = '<div class="verdict"></div>'
    if joined("pista"):
        tail += fold(f'<p>{inline(joined("pista"))}</p>', ui("hint"))
    if joined("solucion"):
        tail += fold(f'<pre><code>{html.escape(joined("solucion"))}</code></pre>',
                     ui("solution"))
    return f'{ask}{body}{tail}</div>'


def fold(inner: str, summary: str) -> str:
    """Wrap a dense block so it is there when wanted and out of the way when not.

    The glossary and the line-by-line code annotations are where a lesson gets heavy.
    Folding them keeps the depth without turning the page into a wall of text.
    """
    return f'<details class="fold"><summary>{summary}</summary>{inner}</details>'


def render_review(content: str) -> str:
    """The review section: every '### question' becomes a collapsible answer."""
    out: list[str] = []
    for chunk in re.split(r"^### +", content, flags=re.M):
        if not chunk.strip():
            continue
        question, _, answer = chunk.partition("\n")
        out.append(
            f"<details><summary>{inline(question.strip())}</summary>"
            f"{render_blocks(answer.split(chr(10)))}</details>"
        )
    return "".join(out)


def _fingerprints() -> dict:
    """Las huellas que dejó figures_theme al dibujar."""
    path = ROOT / "results" / "figuras.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_figure(relative: str, depth: int = 1) -> str:
    """Convierte {{FIG:nombre|pie}} en una figura de dos temas.

    Cada figura existe dos veces, `nombre.claro.png` y `nombre.oscuro.png`, porque
    una figura con fondo de papel dentro de una página en grafito canta como un
    faro. Van las dos al HTML y el CSS enseña la que toca, que es lo único que
    responde tanto a la preferencia del sistema como al interruptor manual.

    La huella del contenido va en la URL y no en el nombre del fichero, que es el
    patrón del portafolio: mata la caché del navegador, y una huella que se mueve
    significa que el dibujo se movió.
    """
    name, _, caption = relative.partition("|")
    name = name.strip()
    huellas = _fingerprints()
    up = "../" * depth

    faltan = [t for t in ("claro", "oscuro")
              if not (FIGURES_DIR / f"{name}.{t}.png").exists()]
    if faltan:
        print(f"  AVISO: falta la figura {name} en {', '.join(faltan)}")
        return f'<p class="gone">falta la figura {html.escape(name)}</p>'

    alt = html.escape(caption.strip() or name.replace("_", " "))
    imagenes = []
    for theme in ("claro", "oscuro"):
        fichero = f"{name}.{theme}.png"
        version = huellas.get(fichero, "")
        query = f"?v={version}" if version else ""
        imagenes.append(
            f'<img class="fig-{theme}" src="{up}figuras/{quote(fichero)}{query}" '
            f'alt="{alt}" loading="lazy">'
        )

    pie = inline(caption.strip()) if caption.strip() else ""
    pie_html = f"<figcaption>{pie}</figcaption>" if pie else ""
    return f'<figure class="fig">{"".join(imagenes)}{pie_html}</figure>'


def render_document(body: str, styles: dict, figures: bool = True) -> str:
    """Turn a Markdown body into the stack of annotated blocks the CSS expects."""
    sections: list[str] = []
    for chunk in re.split(r"^## +", body, flags=re.M):
        if not chunk.strip():
            continue
        heading, _, content = chunk.partition("\n")
        heading = heading.strip()
        modifier, kicker = styles.get(heading.lower(), DEFAULT_STYLE[_lang])
        if heading.lower() in REVIEW_HEADINGS:
            inner = render_review(content)
        else:
            inner = render_blocks(content.split("\n"))
        if heading.lower() in GLOSSARY_HEADINGS:
            terms = content.count("\n- ")
            inner = fold(inner, ui("terms").format(n=terms))
        if figures:
            inner = re.sub(
                r"<p>\{\{FIG:([^}]+)\}\}</p>|\{\{FIG:([^}]+)\}\}",
                # Pages are written to 2_Curso/out/ and the figures live in
                # 2_Curso/figuras/, one level up, so the img src has to climb out of
                # out/. Passing depth=0 here left every figure broken.
                lambda m: resolve_figure(m.group(1) or m.group(2), depth=1),
                inner,
            )
        sections.append(
            f'<section class="block {modifier}">'
            f'<span class="kicker">{html.escape(kicker)}</span>'
            f'<h2 class="block-title">{html.escape(heading)}</h2>'
            f"{inner}</section>"
        )
    return "\n".join(sections)


# ----------------------------------------------------------------------------- page

def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise SystemExit("El archivo tiene que empezar con un bloque --- de front matter.")
    _, block, body = text.split("---", 2)
    meta = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def lesson_stems(syllabus: dict) -> dict[int, str]:
    """Which output file each module writes to, whether or not it exists yet."""
    return {m["number"]: m["slug"] for m in syllabus["modules"]}


def is_written(slug: str, lang: str) -> bool:
    """Whether a module is reachable in a language, decided by its source existing."""
    return (source_dir(lang) / f"{slug}.md").exists()


def page_name(slug: str, lang: str) -> str:
    return f"{quote(slug)}{suffix(lang)}.html"

# Los tramos del lago y los módulos que trabajan sobre cada capa. Viven aquí
# porque los usan las dos plantillas: la barra de la lección y la del índice.
#
# Los rangos son explícitos y no derivados de las partes, porque las partes no
# calzan con las capas: los seis módulos de SQL consultan bronce sin ser una capa
# aparte, y los cuatro de PostgreSQL viven sobre oro. Derivarlos de las partes
# dejaba diez módulos fuera del mapa con dos tramos solapados.
STAGES = [
    ("CRUDO", "RAW", (1, 3)),
    ("BRONCE", "BRONZE", (4, 13)),
    ("PLATA", "SILVER", (14, 16)),
    ("ORO", "GOLD", (17, 22)),
    ("GEMELO", "TWIN", (23, 31)),
]


def build_rail(current: int | None, lang: str) -> str:
    """El grafo del lago en vertical, para la barra de instrumentos.

    Marca qué capa se está construyendo. Sustituye a la tira de números, que con
    treinta y un módulos ocupaba tres filas y no decía nada del recorrido.
    """
    rows = []
    for label_es, label_en, (lo, hi) in STAGES:
        label = label_es if lang == "es" else label_en
        if current is None:
            state = ""
        elif lo <= current <= hi:
            state = " here"
        elif current > hi:
            state = " done"
        else:
            state = ""
        rango = f"{lo}-{hi}" if lo != hi else str(lo)
        rows.append(
            f'<span class="rail-step{state}"><i class="dot"></i>'
            f'<span>{html.escape(label)}</span>'
            f'<span class="range">{rango}</span></span>'
        )
    return "".join(rows)


def part_title(syllabus: dict, module: dict, lang: str) -> str:
    parte = next((p for p in syllabus["partes"] if p["n"] == module.get("parte")), None)
    if not parte:
        return ""
    return (parte.get("title_en") or parte["title"]) if lang == "en" else parte["title"]


def build_thread(syllabus: dict, current: int | None, lang: str = "es") -> str:
    """La tira de módulos: dónde estás, dentro de los 35.

    Silice ponía la cifra de cada módulo dentro de la tira, y con catorce cabía.
    Con treinta y cinco no cabe, y las cifras de este curso son frases enteras
    («3,42 h contra 23,81 h»), así que la tira ocupaba tres filas y no se leía.

    Aquí va solo el número. La cifra y el título viven en el `title`, que es donde
    hacen falta: al pasar por encima, no todo el rato.
    """
    stems = lesson_stems(syllabus)
    parts = []
    previous_part = None
    for module in syllabus["modules"]:
        number = module["number"]
        opens_part = module.get("parte") != previous_part and previous_part is not None
        previous_part = module.get("parte")
        edge = ' class="starts-part"' if opens_part else ""
        label = str(number)
        title = html.escape(
            f"{number}. {module_title(module, lang)} ({cifra_value(module, lang)})",
            quote=True,
        )
        if number == current:
            parts.append(f'<span class="now{" starts-part" if opens_part else ""}" '
                         f'aria-current="page" title="{title}">{label}</span>')
        elif is_written(stems[number], lang):
            parts.append(f'<a{edge} href="{page_name(stems[number], lang)}" '
                         f'title="{title}">{label}</a>')
        else:
            parts.append(f'<span{edge} title="{title} ({UI[lang]["pending"]})" '
                         f'class="gone{" starts-part" if opens_part else ""}">{label}</span>')
    return "".join(parts)


def build_pager(syllabus: dict, current: int, lang: str = "es") -> str:
    """Anterior y siguiente, compactos, porque ahora viven en la barra.

    La versión heredada imprimía el título entero de cada vecino, que en una
    columna de 268 px no cabe. Aquí van el número y la flecha, y el título entra
    en el `title` para quien pase por encima.
    """
    stems = lesson_stems(syllabus)
    numbers = sorted(stems)
    position = numbers.index(current)
    links = []
    for offset, arrow in ((-1, "\u2190"), (1, "\u2192")):
        index = position + offset
        if not (0 <= index < len(numbers)):
            continue
        number = numbers[index]
        if not is_written(stems[number], lang):
            continue
        title = html.escape(f"{number}. {module_title(syllabus['modules'][number - 1], lang)}",
                            quote=True)
        label = f"{arrow} {number}" if offset < 0 else f"{number} {arrow}"
        links.append(f'<a href="{page_name(stems[number], lang)}" title="{title}">{label}</a>')
    return "".join(links)


def build_assay(module: dict, lang: str = "es") -> str:
    """What the module is made of. The honest equivalent of Coursera's video counts."""
    counts = [
        (len(module["figuras"]), UI[lang]["figures"]),
        (len(module["scripts"]), UI[lang]["scripts"]),
    ]
    return "".join(f"<span><b>{count}</b> {label}</span>" for count, label in counts)


def top_link(slug_or_index: str, lang: str) -> tuple[str, str]:
    """The masthead's top-right link and the head's alternate link, as a pair.

    When the twin page exists, both point at it: a real language switch. When it does
    not (a Spanish module not yet translated), the Spanish page offers the English
    summary on the portfolio instead, and declares no alternate.
    """
    twin_lang = other(lang)
    twin_source = "curso.md" if slug_or_index == "index" else f"{slug_or_index}.md"
    if (source_dir(twin_lang) / twin_source).exists():
        href = page_name(slug_or_index, twin_lang)
        link = (f'<a class="portfolio-link" href="{href}" hreflang="{twin_lang}" '
                f'rel="alternate">{html.escape(UI[lang]["switch"])}</a>')
        alternate = f'<link rel="alternate" hreflang="{twin_lang}" href="{href}">'
        return link, alternate
    if lang == "es":
        link = ('<a class="portfolio-link" href="https://kmortizva-data.github.io/work/fuelle.html" '
                f'target="_blank" rel="noopener">{html.escape(UI["es"]["portfolio"])}</a>')
        return link, ""
    return "", ""


def ui_values(lang: str) -> dict[str, str]:
    """The placeholders every template shares, already in the page's language."""
    return {
        "{{LANG}}": lang,
        "{{LANG_SUFFIX}}": suffix(lang),
        "{{UI_MODULE}}": UI[lang]["module"],
        "{{UI_OF}}": UI[lang]["of"],
        "{{UI_THREAD}}": UI[lang]["thread"],
        "{{UI_RAIL}}": UI[lang]["rail"],
        "{{UI_PART}}": UI[lang]["part"],
        "{{UI_WRITTEN}}": UI[lang]["written"],
        "{{UI_MODULES}}": UI[lang]["modules_word"],
        "{{UI_PARTS}}": UI[lang]["parts_word"],
        "{{UI_COURSE}}": UI[lang]["course"],
        "{{UI_TOC_KICKER}}": UI[lang]["toc_kicker"],
        "{{UI_GENERATED}}": UI[lang]["generated"],
        "{{UI_SOURCE}}": UI[lang]["source"],
        "{{SOURCE_NOTE}}": UI[lang]["source_note"],
        "{{COURSE_NAME}}": UI[lang]["course_name"],
        "{{GENERATED}}": date.today().isoformat(),
    }


def build_page(source_path: Path, lang: str | None = None) -> Path:
    if lang is None:
        lang = "en" if source_path.resolve().parent.name == "en" else "es"
    set_language(lang)
    syllabus = load_syllabus()
    meta, body = parse_front_matter(source_path.read_text(encoding="utf-8"))
    number = int(meta["module"])
    module = next((m for m in syllabus["modules"] if m["number"] == number), None)
    if module is None:
        raise SystemExit(f"El módulo {number} no está en temario.json.")
    if source_path.stem != module["slug"]:
        raise SystemExit(f"{source_path.name} no coincide con el slug del temario "
                         f"({module['slug']}). El temario manda.")
    if lang == "en" and not (source_dir("en") / "curso.md").exists():
        raise SystemExit("Falta lecciones/en/curso.md: sin portada inglesa, una lección "
                         "inglesa enlazaría a un índice que no existe.")

    page = (TEMPLATES / "lesson.html").read_text(encoding="utf-8")
    title = module_title(module, lang)
    text_values = {
        "{{PAGE_TITLE}}": UI[lang]["page_title"].format(title=title, n=number),
        "{{MODULE_NUMBER}}": str(number),
        "{{MODULE_TOTAL}}": str(len(syllabus["modules"])),
        "{{MODULE_TITLE}}": title,
        "{{SUBTITLE}}": module_subtitle(module, lang),
        "{{CIFRA_VALUE}}": cifra_value(module, lang),
        "{{CIFRA_LABEL}}": cifra_label(module, lang),
        "{{PART_TITLE}}": part_title(syllabus, module, lang),
        "{{PROGRESS}}": str(round(100 * number / len(syllabus["modules"]))),
        "{{ACCENT}}": module["accent"]["dark"],
        "{{ACCENT_LIGHT}}": module["accent"]["light"],
        "{{ACCENT_DARK}}": module["accent"]["dark"],
        "{{TABLAS}}": tables_for(module),
    }
    text_values.update(ui_values(lang))
    link, alternate = top_link(module["slug"], lang)
    html_values = {
        "{{STYLE}}": load_style(),
        "{{CONTENT}}": render_document(body, SECTION_STYLES[lang]),
        "{{RAIL}}": build_rail(number, lang),
        "{{PAGER}}": build_pager(syllabus, number, lang),
        "{{TOPLINK}}": link,
        "{{ALTERNATE}}": alternate,
    }
    for key, value in text_values.items():
        page = page.replace(key, html.escape(value, quote=True))
    for key, value in html_values.items():
        page = page.replace(key, value)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{module['slug']}{suffix(lang)}.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", help="lesson Markdown files to render")
    parser.add_argument("--all", action="store_true", help="render every lesson written")
    args = parser.parse_args()

    sources = [Path(s) for s in args.sources]
    if args.all:
        sources = sorted(COURSE_DIR.glob(LESSON_GLOB)) + sorted((COURSE_DIR / "en").glob(LESSON_GLOB))
    if not sources:
        raise SystemExit("Nada que renderizar. Pasa un .md o usa --all.")

    for source in sources:
        out_path = build_page(source)
        print(f"{source.name} -> {out_path.relative_to(ROOT)} "
              f"({out_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
