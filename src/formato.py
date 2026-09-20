"""How a number is written, in each edition. One place, because it has bitten twice.

Spanish puts the comma on the decimals and the dot on the thousands, and English
does the opposite. The obvious shortcut, formatting and then replacing on the
whole string, has already eaten the comma of three figure captions in this course
(see `figures_theme.es`), and a second copy of the rule is a second chance to get
it wrong in one edition only.

`figures_theme.es` is the same rule for figures, where the language comes from an
environment variable instead of an argument.
"""

from __future__ import annotations


def numero(v: float, decimales: int, lang: str) -> str:
    """Un número tal como se escribe en el idioma de la página."""
    texto = f"{v:,.{decimales}f}"
    if lang == "es":
        texto = texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return texto
