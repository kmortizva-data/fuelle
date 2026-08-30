"""Build the course: render every lesson written so far, then the front page, twice.

The front page carries three things: what the course is (curso.md), the index of the
modules with the figure each one measured, and the brain file, which is an operating
manual meant to be pasted into an assistant's memory rather than a summary of the lessons.

Modules with no lesson yet show up as pending instead of disappearing, because the plan
is fixed in temario.json from the start and a gap in it should be visible.

Two editions: Spanish from 2_Curso/, English from 2_Curso/en/ (same file names), written
side by side in 2_Curso/out/ as index.html / index.en.html and mNN_slug.html /
mNN_slug.en.html. The English edition is only built once en/curso.md exists, and each
English lesson only once its file exists; every page links its twin when there is one.

Usage:
    python src/site/build_site.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_lesson import (  # noqa: E402  (shared renderer)
    COURSE_DIR, LANGS, OUT_DIR, ROOT, TEMPLATES, UI, build_assay, build_page,
    build_thread, cifra_value, is_written, load_style, load_syllabus, module_subtitle,
    module_title, page_name, render_document, set_language, source_dir, suffix,
    top_link, ui_values,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Section vocabulary of the front page: what the course is, before the modules.
COURSE_SECTION_STYLES = {
    "es": {
        "de qué va este proyecto": ("", "Resumen"),
        "el veredicto, por delante": ("is-result", "Resultado"),
        "el recorrido, módulo a módulo": ("is-method", "Recorrido"),
        "qué sabes hacer al terminar": ("is-bridge", "Resultado"),
        "cómo leer este curso": ("is-toy", "Instrucciones"),
        "de dónde sale todo esto": ("is-terms", "Origen"),
    },
    "en": {
        "what this project is about": ("", "Summary"),
        "the verdict, up front": ("is-result", "Result"),
        "the path, module by module": ("is-method", "The path"),
        "what you can do by the end": ("is-bridge", "Result"),
        "how to read this course": ("is-toy", "Instructions"),
        "where all this comes from": ("is-terms", "Origin"),
    },
}

# Front-page strings that are not lesson text, per language.
INDEX_UI = {
    "es": {
        "eyebrow": "Machine learning desde cero sobre una planta de flotación real",
        "cifra_value": "+0,009",
        "cifra_label": "lo que el ML aportó sobre repetir el último análisis",
        "modules": "Módulos",
        "toc_title": "Las catorce lecciones",
        "memory": "Memoria",
        "brain_title": "El cerebro del proyecto, listo para copiar",
        "brain_text": ("Un manual de operación con las cifras, los umbrales y el veredicto. Se pega "
                       "en la memoria de un asistente y cambia cómo trabaja, sin gastar contexto "
                       "en repetir el proyecto entero."),
        "copy": "Copiar todo", "download": "Descargar",
        "copied": "copiado", "select": "selecciona y copia",
        "notes_count": "apuntes de origen", "figures_count": "figuras",
        "scripts_count": "scripts",
    },
    "en": {
        "eyebrow": "Machine learning from scratch on a real flotation plant",
        "cifra_value": "+0.009",
        "cifra_label": "what ML added over repeating the last assay",
        "modules": "Modules",
        "toc_title": "The fourteen lessons",
        "memory": "Memory",
        "brain_title": "The project's brain, ready to copy (in Spanish)",
        "brain_text": ("An operating manual with the figures, the thresholds and the verdict. "
                       "Paste it into an assistant's memory and it changes how it works, without "
                       "spending context on retelling the whole project. Written in Spanish."),
        "copy": "Copy all", "download": "Download",
        "copied": "copied", "select": "select and copy",
        "notes_count": "source notes", "figures_count": "figures",
        "scripts_count": "scripts",
    },
}

BRAIN_FILE = "cerebro-silice.md"

# The eight bytes every PNG starts with, so a truncated or half-written file is
# caught as well as a missing one.
PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")

warnings: list[str] = []


def build_toc(syllabus: dict, lang: str) -> str:
    """The index: every module, its headline figure, and whether it is written."""
    rows = []
    for module in syllabus["modules"]:
        number = module["number"]
        slug = module["slug"]
        name = (f'<span class="name">{html.escape(module_title(module, lang))}'
                f'<small>{html.escape(module_subtitle(module, lang))}</small></span>')
        mark = f'<span class="mark">{html.escape(cifra_value(module, lang))}</span>'
        number_html = f'<span class="num">{number:02d}</span>'
        if is_written(slug, lang):
            rows.append(f'<li><a href="{page_name(slug, lang)}" '
                        f'style="--accent: {module["accent"]}">'
                        f"{number_html}{name}{mark}</a></li>")
        else:
            rows.append(f'<li><span class="pending">{number_html}{name}'
                        f'<span class="tag">{html.escape(UI[lang]["pending"])}</span></span></li>')
    return "".join(rows)


def build_index(syllabus: dict, written: int, lang: str) -> Path:
    set_language(lang)
    overview = source_dir(lang) / "curso.md"
    brain = COURSE_DIR / "cerebro.md"
    if not overview.exists():
        raise SystemExit(f"Falta {overview.relative_to(ROOT)}, que es la portada del curso.")

    body = overview.read_text(encoding="utf-8")
    if body.startswith("---"):
        _, front, body = body.split("---", 2)

    brain_text = ""
    brain_size = ""
    if brain.exists():
        brain_text = brain.read_text(encoding="utf-8")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / BRAIN_FILE).write_text(brain_text, encoding="utf-8")
        brain_size = f"{len(brain_text.encode('utf-8')) / 1024:.1f} KB"
    elif lang == "es":
        warnings.append("no hay cerebro.md, la portada se queda sin archivo de memoria")

    strings = INDEX_UI[lang]
    total = len(syllabus["modules"])
    assay = (f"<span><b>{written}</b> {UI[lang]['of']} {total} {UI[lang]['lessons']}</span>"
             f"<span><b>31</b> {strings['notes_count']}</span>"
             f"<span><b>40</b> {strings['figures_count']}</span>"
             f"<span><b>39</b> {strings['scripts_count']}</span>")

    subtitle = (syllabus.get("course_subtitle_en") or syllabus["course_subtitle"]) \
        if lang == "en" else syllabus["course_subtitle"]
    page = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    text_values = {
        "{{PAGE_TITLE}}": f'{UI[lang]["course_name"]} · {subtitle}',
        "{{EYEBROW}}": strings["eyebrow"],
        "{{SUBTITLE}}": subtitle,
        "{{CIFRA_VALUE}}": strings["cifra_value"],
        "{{CIFRA_LABEL}}": strings["cifra_label"],
        "{{ACCENT}}": syllabus["modules"][6]["accent"],
        "{{BRAIN_FILE}}": BRAIN_FILE,
        "{{BRAIN_SIZE}}": brain_size,
        "{{UI_MODULES}}": strings["modules"],
        "{{UI_TOC_TITLE}}": strings["toc_title"],
        "{{UI_MEMORY}}": strings["memory"],
        "{{UI_BRAIN_TITLE}}": strings["brain_title"],
        "{{UI_BRAIN_TEXT}}": strings["brain_text"],
        "{{UI_COPY}}": strings["copy"],
        "{{UI_DOWNLOAD}}": strings["download"],
        "{{UI_COPIED}}": strings["copied"],
        "{{UI_SELECT}}": strings["select"],
    }
    text_values.update(ui_values(lang))
    link, alternate = top_link("index", lang)
    html_values = {
        "{{STYLE}}": load_style(),
        "{{CONTENT}}": render_document(body, COURSE_SECTION_STYLES[lang]),
        "{{THREAD}}": build_thread(syllabus, None, lang),
        "{{TOC}}": build_toc(syllabus, lang),
        "{{ASSAY}}": assay,
        "{{BRAIN}}": html.escape(brain_text),
        "{{TOPLINK}}": link,
        "{{ALTERNATE}}": alternate,
    }
    for key, value in text_values.items():
        page = page.replace(key, html.escape(value, quote=True))
    for key, value in html_values.items():
        page = page.replace(key, value)

    out_path = OUT_DIR / f"index{suffix(lang)}.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


def check_figure_links() -> None:
    """Resolve every img src against the filesystem, the way file:// will.

    The pages are written to 2_Curso/out/ and the figures live one level up in
    2_Curso/figuras/, so the src has to climb out of out/. Getting that wrong left all
    seven figures of the first lesson broken while every checker stayed green, because
    none of them looked at the generated HTML. This does.
    """
    import re

    for page in sorted(OUT_DIR.glob("*.html")):
        for src in re.findall(r'<img[^>]+src="([^"]+)"', page.read_text(encoding="utf-8")):
            target = (page.parent / src).resolve()
            if not target.is_file():
                warnings.append(f"{page.name}: la figura {src} no existe en disco")
            elif target.open("rb").read(8) != PNG_MAGIC:
                warnings.append(f"{page.name}: {src} no es un PNG valido")


def check_twin_links() -> None:
    """Every href inside out/ has to land on a file: a switch to nowhere is a bug."""
    import re

    for page in sorted(OUT_DIR.glob("*.html")):
        for href in re.findall(r'href="([^"#]+)"', page.read_text(encoding="utf-8")):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if not (page.parent / href).resolve().exists():
                warnings.append(f"{page.name}: el enlace {href} no existe")


def main() -> None:
    syllabus = load_syllabus()
    total = len(syllabus["modules"])

    for lang in LANGS:
        if lang == "en" and not (source_dir("en") / "curso.md").exists():
            print("  (sin edición inglesa todavía: falta 2_Curso/en/curso.md)")
            continue
        written = 0
        for module in syllabus["modules"]:
            source = source_dir(lang) / f"{module['slug']}.md"
            if not source.exists():
                continue
            out_path = build_page(source, lang)
            written += 1
            print(f"  {lang} módulo {module['number']:>2}  {out_path.name:<48} "
                  f"{out_path.stat().st_size:>8,} bytes")
        index = build_index(syllabus, written, lang)
        print(f"  {lang} {written}/{total} lecciones · {index.relative_to(ROOT)} "
              f"({index.stat().st_size:,} bytes)")

    check_figure_links()
    check_twin_links()

    figures = len(list((COURSE_DIR / "figuras").glob("*.png")))
    print(f"\n{figures} figuras")
    if not figures:
        warnings.append("no hay ni una figura convertida todavía: "
                        "python src/site/convert_figures.py")
    if warnings:
        print(f"\nAVISOS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
