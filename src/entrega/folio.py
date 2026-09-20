"""The verdict on one sheet of A4, in both languages. Module 31.

The last deliverable is the one a plant would actually read: the question, the
method in five lines, the table, what the twin does not do, and what would break
in a real plant. One page, and every number on it measured.

**Nothing is typed.** `lecciones/folio.md` carries holes like `{umbral}` instead
of figures, this file fills them from `results/`, and then it reads its own
output back and refuses to write if any number in it is not in a results file.
Writing the folio by hand would have been faster and would have put the course's
credibility in the hands of my copying.

It is an HTML page and not a LaTeX document on purpose. The plan said Tectonic,
and Tectonic is 47 MB that the repository's privacy guard would reject, a second
visual system to maintain, and one more thing to install for whoever clones this.
The page is printed to PDF with `src/entrega/imprime.py`, it carries the same
fonts and colours as the course, and it is also a page the portfolio can link.

Run:  .venv\\Scripts\\python.exe src\\entrega\\folio.py
"""

from __future__ import annotations

import html
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC / "site"))

import check_numbers  # noqa: E402
from formato import numero  # noqa: E402
from render_lesson import inline, render_blocks, set_language  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = SRC.parent
LESSONS = PROJECT / "lecciones"
RESULTS = PROJECT / "results"
OUT = PROJECT / "out"
TEMPLATES = SRC / "site" / "templates"
PROPIO = RESULTS / "m31_folio.json"

# El módulo del que sale el acento, y el que cuenta cómo se hizo esto.
MODULO = 31

UI = {
    "es": {
        "titulo": "El veredicto en un folio · Fuelle",
        "descripcion": "El veredicto del gemelo digital de un compresor de aire, en una cara: "
                       "qué detecta, con cuántas falsas alarmas, y qué se rompería en una "
                       "planta de verdad.",
        "ceja": "gemelo digital del compresor de aire de un tren",
        "meta": "Kevin Ortiz\nkmortizva-data.github.io",
        "generado": "generado el",
        "fuente": "fuente",
        "nota_fuente": "MetroPT-3, del compresor de un tren del Metro de Oporto (CC BY 4.0)",
        "acciones": [("index.html", "el curso"), ("panel.html", "el panel"),
                     ("veredicto.pdf", "descargar el PDF"), ("folio.en.html", "English")],
    },
    "en": {
        "titulo": "The verdict on one page · Bellows",
        "descripcion": "The verdict of a digital twin of an air compressor, on one side of a "
                       "sheet: what it catches, at how many false alarms, and what would break "
                       "in a real plant.",
        "ceja": "digital twin of a train's air compressor",
        "meta": "Kevin Ortiz\nkmortizva-data.github.io",
        "generado": "generated on",
        "fuente": "source",
        "nota_fuente": "MetroPT-3, from a Porto Metro train compressor (CC BY 4.0)",
        "acciones": [("index.en.html", "the course"), ("panel.en.html", "the panel"),
                     ("verdict.pdf", "download the PDF"), ("folio.html", "Español")],
    },
}

PDF = {"es": "veredicto.pdf", "en": "verdict.pdf"}


def lee(nombre: str) -> dict:
    return json.loads(io.open(RESULTS / f"{nombre}.json", encoding="utf-8").read())


def cifras(lang: str) -> dict[str, str]:
    """Cada hueco del folio, con el fichero de resultados del que sale.

    El umbral y las cuentas del veredicto se leen del barrido del módulo 28, no
    de una constante: si el barrido eligiera otro umbral, el folio lo seguiría.
    """
    m01, m24, m27 = lee("m01_raw"), lee("m24_fisica"), lee("m27_residual")
    m28, m30 = lee("m28_veredicto"), lee("m30_panel")
    temario = json.loads(io.open(PROJECT / "temario.json", encoding="utf-8").read())

    principal = m28["barridos"]["congelado, marzo no cuenta"]
    umbral = max(b["umbral"] for b in principal if b["detectados"] == b["sucesos"])
    fila = next(b for b in principal if b["umbral"] == umbral)
    con_marzo = next(b for b in m28["barridos"]["congelado, marzo cuenta"]
                     if b["umbral"] == umbral)
    lps = m28["rival_instalado"]
    agosto = next(d for d in m27["deriva"] if d["mes"] == "2020-08")

    return {
        "lecturas": numero(m01["rows"], 0, lang),
        "senales": str(m01["n_signals"]),
        "mb_csv": numero(m01["size_mb"], 1, lang),
        "arranca": numero(m24["arranca"], 2, lang),
        "para": numero(m24["para"], 2, lang),
        "llena": numero(m24["llena"], 4, lang),
        "consumo": numero(m24["consumo"], 4, lang),
        "descuadre": numero(m24["balance"]["descuadre_pct"], 1, lang),
        "umbral": numero(umbral, 2, lang),
        "dias_juzgados": numero(m28["rival_del_ciclo"]["dias"], 0, lang),
        "detectados": str(fila["detectados"]),
        "sucesos": str(fila["sucesos"]),
        "dias_alarma": str(fila["dias_con_alarma"]),
        "falsas_mes": numero(fila["falsas_por_mes"], 1, lang),
        "lps_detectados": str(lps["de_cuatro_partes"]),
        "lps_dias": str(lps["dias_con_alarma"]),
        "lps_falsas_mes": numero(lps["falsas_por_mes"], 1, lang),
        "marzo_detectados": str(con_marzo["detectados"]),
        "marzo_sucesos": str(con_marzo["sucesos"]),
        "marzo_falsas": numero(con_marzo["falsas_por_mes"], 1, lang),
        "agosto_alto": str(agosto["sobre_el_suelo"]),
        "agosto_dias": str(agosto["dias"]),
        "modulos": str(len(temario["modules"])),
        "dias_panel": str(m30["dias"]),
    }


def rellena(texto: str, valores: dict[str, str]) -> str:
    """Los huecos, uno a uno, y un aviso si queda alguno sin llenar."""
    def cambia(m: re.Match) -> str:
        clave = m.group(1)
        if clave not in valores:
            raise SystemExit(f"El folio pide «{clave}» y no está entre las cifras medidas. "
                             f"Añádela a cifras() con el fichero de results de donde sale.")
        return valores[clave]

    return re.sub(r"\{([a-z_]+)\}", cambia, texto)


def renderiza(texto: str) -> tuple[str, str]:
    """El título y el cuerpo. Las secciones son `## `, como en las lecciones."""
    lineas = texto.splitlines()
    titulos = [l[2:].strip() for l in lineas if l.startswith("# ")]
    if len(titulos) != 1:
        raise SystemExit("El folio tiene que empezar con un único título de primer nivel.")
    cuerpo = "\n".join(l for l in lineas if not l.startswith("# "))

    partes = [f"<h1>{inline(titulos[0])}</h1>"]
    for trozo in re.split(r"^## +", cuerpo, flags=re.M):
        if not trozo.strip():
            continue
        cabeza, _, resto = trozo.partition("\n")
        partes.append(f"<h2>{inline(cabeza.strip())}</h2>")
        partes.append(render_blocks(resto.split("\n")))
    return titulos[0], "".join(partes)


def sin_marcado(html_texto: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html_texto).split())


def numeros_sin_respaldo(texto: str, lang: str, conocidos: set) -> list[str]:
    """Los números del folio que ningún script ha escrito en `results/`.

    Es la misma puerta que `check_numbers` pone a las lecciones, aplicada aquí
    porque el folio no es una lección y se quedaría fuera de ella. Un folio con
    una cifra a mano vale menos que no tener folio.
    """
    fuera = []
    for m in check_numbers.NUMBER.finditer(texto):
        valor = check_numbers.canonical(m.group(), lang)
        if valor is None or valor in conocidos:
            continue
        fuera.append(m.group())
    return fuera


def construye(lang: str, conocidos: set) -> Path:
    set_language(lang)
    ui = UI[lang]
    fuente = (LESSONS if lang == "es" else LESSONS / "en") / "folio.md"
    if not fuente.exists():
        raise SystemExit(f"Falta {fuente.relative_to(PROJECT)}, el texto del folio.")

    valores = cifras(lang)
    titulo, cuerpo = renderiza(rellena(fuente.read_text(encoding="utf-8"), valores))

    sueltos = numeros_sin_respaldo(sin_marcado(cuerpo), lang, conocidos)
    if sueltos:
        raise SystemExit(f"El folio ({lang}) enseña {len(sueltos)} números que no salen de "
                         f"ninguna corrida: {', '.join(sueltos[:6])}. Se miden o se quitan.")

    temario = json.loads(io.open(PROJECT / "temario.json", encoding="utf-8").read())
    acento = next(m for m in temario["modules"] if m["number"] == MODULO)["accent"]["light"]
    acciones = "".join(f'<a href="{href}">{html.escape(texto)}</a>'
                       for href, texto in ui["acciones"])

    pagina = (TEMPLATES / "folio.html").read_text(encoding="utf-8")
    texto = {
        "{{LANG}}": lang,
        "{{PAGE_TITLE}}": ui["titulo"],
        "{{DESCRIPTION}}": ui["descripcion"],
        "{{COURSE_NAME}}": "Fuelle" if lang == "es" else "Bellows",
        "{{EYEBROW}}": ui["ceja"],
        "{{UI_GENERATED}}": ui["generado"],
        "{{UI_SOURCE}}": ui["fuente"],
        "{{SOURCE_NOTE}}": ui["nota_fuente"],
        "{{GENERATED}}": date.today().isoformat(),
        "{{ACCENT_LIGHT}}": acento,
    }
    otro = "en" if lang == "es" else "es"
    marcado = {
        "{{STYLE}}": (TEMPLATES / "_base.css").read_text(encoding="utf-8"),
        "{{FOLIO_STYLE}}": (TEMPLATES / "_folio.css").read_text(encoding="utf-8"),
        "{{CONTENT}}": cuerpo,
        "{{META}}": "<br>".join(html.escape(l) for l in ui["meta"].splitlines()),
        "{{ACTIONS}}": acciones,
        "{{ALTERNATE}}": f'<link rel="alternate" hreflang="{otro}" '
                         f'href="folio{"" if otro == "es" else ".en"}.html">',
    }
    for clave, valor in texto.items():
        pagina = pagina.replace(clave, html.escape(valor, quote=True))
    for clave, valor in marcado.items():
        pagina = pagina.replace(clave, valor)
    if "{{" in pagina:
        raise SystemExit(f"El folio ({lang}) deja una llave sin rellenar: "
                         f"{pagina[pagina.index('{{'):][:40]}")

    OUT.mkdir(parents=True, exist_ok=True)
    destino = OUT / f"folio{'' if lang == 'es' else '.en'}.html"
    destino.write_text(pagina, encoding="utf-8")
    print(f"  {destino.name:<16} {titulo[:44]:<46} {len(sin_marcado(cuerpo).split()):>4} palabras")
    return destino


def main() -> None:
    # El fichero propio se borra antes de leer lo medido: si se quedara, el folio
    # podría justificar sus números con los suyos de la corrida anterior.
    PROPIO.unlink(missing_ok=True)
    conocidos = check_numbers.measured()

    paginas = {lang: construye(lang, conocidos) for lang in ("es", "en")}
    valores = cifras("es")
    payload = {
        "paginas": {lang: p.name for lang, p in paginas.items()},
        "pdf": PDF,
        "palabras": {lang: len(sin_marcado(
            renderiza(rellena(((LESSONS if lang == "es" else LESSONS / "en")
                               / "folio.md").read_text(encoding="utf-8"), cifras(lang)))[1]
        ).split()) for lang in ("es", "en")},
        "cifras_del_folio": len(valores),
        "rupturas": (LESSONS / "folio.md").read_text(encoding="utf-8").split(
            "## Qué se rompería en una planta de verdad")[-1].count("\n- "),
    }
    with io.open(PROPIO, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"  {payload['rupturas']} cosas que se romperían, y {payload['cifras_del_folio']} "
          f"cifras, todas medidas")
    print(f"  escrito en {PROPIO.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
