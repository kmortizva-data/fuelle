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
COURSE_DIR = ROOT / "2_Curso"

# A lesson file is m<NN>_<slug>.md. The pattern is this strict because Windows
# matches globs case-insensitively, so a loose "m*.md" also picked up MANUAL.md and
# reported the manual for quoting the very phrases it bans.
LESSON_GLOB = "m[0-9][0-9]_*.md"

FIGURES_DIR = COURSE_DIR / "figuras"
OUT_DIR = COURSE_DIR / "out"
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
        "course_name": "Sílice",
        "page_title": "{title} · Sílice, módulo {n}",
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
        "source_note": "los 31 apuntes originales, sus scripts y el CSV de la planta",
        "pending": "pendiente",
        "switch": "English",
        "portfolio": "English summary on the portfolio ↗",
    },
    "en": {
        "course_name": "Silica",
        "page_title": "{title} · Silica, module {n}",
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
        "source_note": "the 31 original notes, their scripts and the plant CSV",
        "pending": "pending",
        "switch": "Español",
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
    return json.loads((COURSE_DIR / "temario.json").read_text(encoding="utf-8"))


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


def figure_files(name: str, lang: str) -> list[Path]:
    """The rasterised figures for `name`, in the language asked for.

    A figure is `fig_m9_pca.a3f2c1d0.png` in Spanish and `fig_m9_pca.en.a3f2c1d0.png` in
    English, so a plain glob of `fig_m9_pca.*.png` matches both and a Spanish page could
    end up serving the English drawing. The fingerprint is eight hex characters, which is
    what tells the two apart.

    English falls back to the Spanish figure when its twin has not been drawn yet. That is
    the honest state while the redraw is in progress: an English caption over a Spanish
    axis reads worse than it should, but a missing figure reads as a bug.
    """
    if not FIGURES_DIR.is_dir():
        return []
    spanish = re.compile(rf"^{re.escape(name)}\.[0-9a-f]{{8}}\.png$")
    english = re.compile(rf"^{re.escape(name)}\.en\.[0-9a-f]{{8}}\.png$")
    wanted = english if lang == "en" else spanish
    matches = sorted(p for p in FIGURES_DIR.iterdir() if wanted.match(p.name))
    if matches or lang != "en":
        return matches
    return sorted(p for p in FIGURES_DIR.iterdir() if spanish.match(p.name))


def resolve_figure(relative: str, depth: int = 1) -> str:
    """Turn a {{FIG:name|caption}} directive into a figure.

    The lesson asks for `fig_m2_arbol` and the file on disk is `fig_m2_arbol.a3f2c1d0.png`:
    every figure carries a fingerprint of its own image, so a browser cannot serve a stale
    copy and a moved fingerprint means the drawing itself moved.
    """
    name, _, caption = relative.partition("|")
    name = name.strip()
    matches = figure_files(name, _lang)
    if not matches:
        print(f"  AVISO: falta la figura {name}")
        return f'<p class="gone">falta la figura {html.escape(name)}</p>'
    target = matches[-1]
    up = "../" * depth
    return (f'<figure class="fig"><img src="{up}figuras/{quote(target.name)}" '
            f'alt="{html.escape(caption.strip() or name)}" loading="lazy">'
            f'<figcaption>{inline(caption.strip()) or html.escape(name)}</figcaption>'
            f"</figure>")


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


def build_thread(syllabus: dict, current: int | None, lang: str = "es") -> str:
    """The segment strip: where you are, and what every module measured."""
    stems = lesson_stems(syllabus)
    parts = []
    previous_part = None
    for module in syllabus["modules"]:
        number = module["number"]
        opens_part = module.get("parte") != previous_part and previous_part is not None
        previous_part = module.get("parte")
        edge = ' class="starts-part"' if opens_part else ""
        label = (f'<span class="n">{number}</span> '
                 f'<span class="v">{html.escape(cifra_value(module, lang))}</span>')
        title = html.escape(f"{number}. {module_title(module, lang)}", quote=True)
        # Whether a module is reachable is decided by its source existing, not by its
        # output: otherwise the strip depends on the order the pages happen to be built
        # in, and the first module of a fresh build links to nothing.
        if number == current:
            parts.append(f'<span{edge} aria-current="page" title="{title}">{label}</span>')
        elif is_written(stems[number], lang):
            parts.append(f'<a{edge} href="{page_name(stems[number], lang)}" '
                         f'title="{title}">{label}</a>')
        else:
            parts.append(f'<span{edge} title="{title} ({UI[lang]["pending"]})">{label}</span>')
    return "".join(parts)


def build_pager(syllabus: dict, current: int, lang: str = "es") -> str:
    modules = {m["number"]: m for m in syllabus["modules"]}
    stems = lesson_stems(syllabus)
    parts = []
    for number, direction, css in ((current - 1, UI[lang]["prev"], "prev"),
                                   (current + 1, UI[lang]["next"], "next")):
        module = modules.get(number)
        if not module or not is_written(stems[number], lang):
            continue
        parts.append(
            f'<a class="{css}" href="{page_name(stems[number], lang)}">'
            f'<span class="dir">{direction}</span>'
            f'{number}. {html.escape(module_title(module, lang))}</a>'
        )
    return "".join(parts)


def build_assay(module: dict, lang: str = "es") -> str:
    """What the module is made of. The honest equivalent of Coursera's video counts."""
    counts = [
        (len(module["apuntes"]), UI[lang]["notes"]),
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
        link = ('<a class="portfolio-link" href="https://kmortizva-data.github.io/work/silica.html" '
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
        raise SystemExit("Falta 2_Curso/en/curso.md: sin portada inglesa, una lección "
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
        "{{ACCENT}}": module["accent"],
    }
    text_values.update(ui_values(lang))
    link, alternate = top_link(module["slug"], lang)
    html_values = {
        "{{STYLE}}": load_style(),
        "{{CONTENT}}": render_document(body, SECTION_STYLES[lang]),
        "{{THREAD}}": build_thread(syllabus, number, lang),
        "{{PAGER}}": build_pager(syllabus, number, lang),
        "{{ASSAY}}": build_assay(module, lang),
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
