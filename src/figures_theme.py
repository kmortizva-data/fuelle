"""Cada figura, dos veces: una para el tema claro y otra para el oscuro.

El curso respeta el interruptor de tema del navegador, así que una figura con
fondo de papel dentro de una página en grafito canta como un faro. La solución
que ya funciona en Sílice para los dos idiomas se copia aquí para los dos temas:
**los scripts de figuras no se tocan**. Dibujan una vez, y este módulo se encarga
de correrlos dos veces cambiando solo los colores y el destino del `savefig`.

Los colores no se eligen aquí: salen de `results/palette.json`, que genera
`src/site/palette.py` en OKLCH midiendo el contraste. Si la paleta cambia, las
figuras cambian con ella.

Uso desde un script de figuras:

    from figures_theme import figura

    def dibujar(fig, ax, c):
        ax.plot(x, y, color=c["accent"])

    figura("fig_m01_averias", dibujar, ancho=9, alto=3.4)

`figura` llama a `dibujar` una vez por tema y guarda las dos versiones.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figures_i18n  # noqa: E402

# El idioma se resuelve aquí y en ningún otro sitio. Los 16 scripts de figuras
# importan este módulo, y aquí pyplot ya está importado, que es justo lo que
# necesita el parche de `savefig` para que pyplot no lo rechace. En español no
# hace nada, así que la llamada va sin condiciones.
figures_i18n.install()

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
FIGURES = PROJECT / "figuras"
PALETTE = PROJECT / "results" / "palette.json"

# Los dos temas, con los mismos tokens que el CSS. Si estos y `_base.css` se
# separan, las figuras dejan de pertenecer a la página.
THEMES = {
    "claro": {
        "ground": "#fbfaf8", "panel": "#e9e6e0", "ink": "#191d20",
        "ink_soft": "#4c545a", "ink_faint": "#7c868d", "rule": "#d6d1c8",
    },
    "oscuro": {
        "ground": "#14181b", "panel": "#171c20", "ink": "#e2e7ea",
        "ink_soft": "#a6b0b6", "ink_faint": "#717e85", "rule": "#293036",
    },
}


def _palette() -> dict:
    return json.loads(io.open(PALETTE, encoding="utf-8").read())


def colours(theme: str, module: int | None = None) -> dict:
    """Los colores de un tema, con el acento del módulo si se pide."""
    palette = _palette()
    key = "dark" if theme == "oscuro" else "light"
    series = palette["fixed"]["series"][key]
    out = dict(THEMES[theme])
    out["measured"] = series["measured"]
    out["simulated"] = series["simulated"]
    if module is not None:
        out["accent"] = palette["accents"][module - 1][key]
    else:
        out["accent"] = series["measured"]
    return out


def _style(theme: str, c: dict) -> dict:
    """El estilo de matplotlib para un tema. Nada de rejillas ni marcos de más."""
    return {
        "figure.facecolor": c["ground"],
        "axes.facecolor": c["ground"],
        "savefig.facecolor": c["ground"],
        "text.color": c["ink"],
        "axes.labelcolor": c["ink_soft"],
        "axes.edgecolor": c["rule"],
        "xtick.color": c["ink_faint"],
        "ytick.color": c["ink_faint"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": c["rule"],
        "grid.linewidth": 0.6,
        # Plex Mono para los números de los ejes, que es lo que usa la página.
        "font.family": "monospace",
        "font.monospace": ["IBM Plex Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono"],
        "font.size": 9,
        "axes.titlesize": 10,
        "figure.dpi": 150,
    }


def es(n: float, decimales: int = 0) -> str:
    """Un número en el idioma de la figura: 1.516.948 en español, 1,516,948 en inglés.

    Existe porque el atajo evidente, formatear y hacer `.replace(",", ".")`
    sobre la cadena entera, ya ha estropeado tres etiquetas de este curso: se
    come también la coma de la prosa y convierte «un día lleno, 8.640 lecturas»
    en «un día lleno. 8.640 lecturas». El cambio de separador tiene que hacerse
    sobre el número solo, y por eso vive aquí y no suelto en cada figura.

    Y por eso mismo es el sitio donde se decide el idioma del número. El parche de
    `figures_i18n` no puede hacerlo: descarta los números al buscar traducciones,
    porque reportarlos todos como «sin traducir» ahogaría la lista que hay que
    revisar. Así que un «1.516.948» se colaba entero en la figura inglesa y la
    puerta daba verde.
    """
    ingles = f"{n:,.{decimales}f}"
    if figures_i18n.language() != "es":
        return ingles
    return ingles.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def fingerprint(path: Path) -> str:
    # `destino` resuelve el idioma en curso. Sin ella, durante una corrida
    # inglesa se leería `fig_x.claro.png`, que existe porque es la española, y la
    # huella publicada no correspondería con el fichero recién escrito.
    return hashlib.sha256(figures_i18n.destino(path).read_bytes()).hexdigest()[:8]


def figura(name: str, dibujar, ancho: float = 9.0, alto: float = 3.6,
           module: int | None = None) -> None:
    """Dibuja una vez, guarda dos.

    `dibujar` recibe `(fig, ax, colores)` y se llama una vez por tema. No es un
    gestor de contexto porque un `with` solo puede ceder una vez, y aquí hace
    falta ejecutar el mismo dibujo dos veces: si se dibujara una y se recolorease
    después, cualquier color puesto a mano en el cuerpo se quedaría fuera.
    """
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(ancho, alto))
            dibujar(fig, ax, c)
            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            escrito = figures_i18n.destino(target)
            print(f"  {escrito.name:<47} {escrito.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")


def guardar_huellas(nombres: list[str]) -> None:
    """Deja las huellas en results/, para que se vea si un dibujo se movió."""
    salida = PROJECT / "results" / "figuras.json"
    datos = {}
    if salida.exists():
        datos = json.loads(io.open(salida, encoding="utf-8").read())
    for name in nombres:
        for theme in ("claro", "oscuro"):
            # Solo el idioma en curso: una corrida inglesa no tiene por qué
            # recalcular la huella española, y al revés tampoco.
            f = figures_i18n.destino(FIGURES / f"{name}.{theme}.png")
            if f.exists():
                datos[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()[:8]
    io.open(salida, "w", encoding="utf-8").write(
        json.dumps(dict(sorted(datos.items())), ensure_ascii=False, indent=2) + "\n"
    )
    print(f"  huellas en {salida.relative_to(PROJECT)}")
