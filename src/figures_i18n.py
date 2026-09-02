"""Draw the course figures in English without touching the 16 scripts that draw them.

The figures were written in Spanish, and they are the part of this course that has
been checked by eye the most. Rewriting their labels across 16 files to add a
language would put every one of those drawings back at risk for nothing: the
geometry, the data and the palette are already right, only the words are Spanish.

So the words are replaced at the moment matplotlib sets them. Three patches are
enough, because every visible string and every saved file passes through one:

  - `Text.set_text`, where a title, an axis label, an annotation and a tick label
    all end up, whatever method asked for them.
  - `Artist.set_label`, where `plot(..., label="x")` puts the legend entry.
  - `Figure.savefig`, which writes `fig_m17_linaje_dbt.claro.en.png` so a Spanish
    figure is never overwritten by its twin.

**Why patching and not a language argument.** Only 6 of the 16 scripts go through
`figures_theme.figura()`; the other 10 run their own theme loop and their own
`savefig`. A language loop inside `figura()` would cover six of them. Patching
`savefig` covers all sixteen, and that is the same reason the Silice course does
it this way.

Lookups are normalised (no accents, lower case, whitespace collapsed) so a label
built with an f-string matches the same entry as its literal twin.

Anything visible with no translation is collected and reported. A figure that
quietly keeps a Spanish axis is the failure this module exists to prevent.

Usage, from the runner, with pyplot imported before install():

    import figures_i18n
    figures_i18n.install()      # no-op unless FIG_LANG=en
    ...
    figures_i18n.report()
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

# Cadenas iguales en los dos idiomas, así que su ausencia de la tabla no es un
# hueco: unidades, nombres de señal del compresor, notación y números.
NEUTRAL = {
    "", "-", "...", "ok", "sql", "csv", "json", "dbt", "duckdb", "postgresql",
    "delta", "iceberg", "parquet", "bar", "kb", "mb", "gb", "utc", "api",
    # Las quince señales del fichero, que son nombres de columna y no prosa.
    "tp2", "tp3", "h1", "dv_pressure", "reservoirs", "oil_temperature",
    "motor_current", "comp", "dv_eletric", "towers", "mpg", "lps",
    "pressure_switch", "oil_level", "caudal_impulses", "timestamp", "day",
    # Los nombres que el propio proyecto da a sus tablas y a sus modelos, que
    # salen en español en las dos ediciones porque son identificadores: el grafo
    # del módulo 17 los lee del manifest de dbt, y traducirlos rompería el enlace
    # con los ficheros que los producen.
    #
    # OJO: aquí NO va `lecturas`. Está en el lago como nombre de columna, pero en
    # la figura del módulo 9 es el rótulo del eje, o sea prosa, y meterlo aquí la
    # dejó en español sin que nadie lo reportara. Un nombre de columna que además
    # es una palabra corriente no se puede neutralizar a ciegas.
    "plata", "clima", "averias", "oro_ciclo_diario", "oro_horas", "oro_averias",
    "prep_telemetria", "prep_clima", "prep_averias", "source_index",
    # Palabras clave de SQL, que son las mismas en cualquier idioma.
    "inner join", "left join", "cross join", "select", "group by",
}

# Familias enteras que nunca hay que traducir, sobre la cadena normalizada.
NEUTRAL_PATTERNS = (
    r"^\$\\mathdefault\{.*\}\$$",          # etiquetas de eje logarítmico
    r"^[\d.,]+ ?(s|ms|kb|mb|gb|bar|h|%)?$",  # números con o sin unidad
    r"^\d{4}-\d{2}(-\d{2})?$",             # fechas ISO
    # Solo los meses INGLESES, que son nuestra propia salida. Los españoles
    # estaban aquí y fue un error: dejaron el eje del módulo 8 con «abr» y «ago»
    # en la figura inglesa, y la puerta ni los mencionó. Neutralizar de más es
    # tan peligroso como no traducir: apaga el aviso.
    r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$",
    r"^fig_m\d+",                          # nombres de fichero de figura
    # `lecturas.tp2`, `dias.dia`: tabla y columna de PostgreSQL, o sea
    # identificadores del esquema. Traducirlos rompería el enlace con la base.
    r"^(lecturas|dias|origen)\.\w+$",
)

# La tabla, escrita en español legible: las claves se normalizan al final del
# módulo, así que aquí se pueden poner con acentos y mayúsculas.
#
# Arrancó vacía a propósito. Correr `figures_build_en.py` sin tabla imprime todas
# las cadenas visibles que quedan en español, y esa lista es la tabla: no hay que
# leer los 16 scripts a mano buscando etiquetas.
TRADUCCIONES: dict[str, str] = {
    # --- módulo 1, el encargo ------------------------------------------
    "los 10 s que promete la ficha": "the 10 s the datasheet promises",
    "hueco, s": "gap, s",
    "lecturas (escala logarítmica)": "readings (log scale)",
    "4 partes de avería": "4 failure reports",

    # --- módulo 2, dato, tabla y tipo ----------------------------------
    "analógica: 3.683 valores distintos": "analogue: 3,683 distinct values",
    "digital: 2 valores, y nada en medio": "digital: 2 values, and nothing between",
    "presión del compresor TP2, en bar": "compressor pressure TP2, in bar",
    "valores distintos en la columna (escala logarítmica)":
        "distinct values in the column (log scale)",

    # --- módulo 3, dónde viven los datos -------------------------------
    "un fichero de texto": "a text file",
    "un lago de ficheros": "a lake of files",
    "una base de datos": "a database",
    "un almacén": "a warehouse",
    "contar filas": "counting rows",
    "una columna": "one column",
    "siete columnas": "seven columns",
    "segundos (escala logarítmica)": "seconds (log scale)",

    # --- módulo 4, bronce ----------------------------------------------
    "lecturas en la partición": "readings in the partition",
    "día completo": "complete day",
    "día incompleto": "incomplete day",

    # --- módulo 5, idempotencia y huella -------------------------------
    "sin huella: vuelve a ingerir siempre": "no fingerprint: it ingests every time",
    "con huella: solo si el origen cambió": "with fingerprint: only if the source moved",
    "veces que se corre la misma ingesta": "times the same ingestion is run",
    "millones de filas en el destino": "millions of rows written",
    "lo que hay en el origen": "what the source holds",

    # --- módulo 6, particionar -----------------------------------------
    "1\nun fichero": "1\none file",
    "8\npor mes": "8\nby month",
    "32\npor semana": "32\nby week",
    "212\npor día": "212\nby day",
    "ficheros en que se parte la tabla": "files the table is split into",
    "segundos en leer un día": "seconds to read one day",
    "segundos, mediana de 7 corridas y su rango (escala logarítmica)":
        "seconds, median of 7 runs and its range (log scale)",

    # --- módulo 7, filas contra columnas -------------------------------
    "KB que ocupa la columna dentro del fichero": "KB the column takes inside the file",
    "tamaño en disco, MB": "size on disk, MB",
    "MB que ocupa el total": "MB the whole thing takes",

    # --- módulo 8, la primera consulta ---------------------------------
    # Los meses del eje, que este módulo escribe a mano en español.
    #
    # SOLO los cuatro que cambian. Poner también los ocho iguales, «feb» a «feb»,
    # parecía más completo y rompió el módulo 18: allí las etiquetas las pone
    # matplotlib con `%b`, o sea «Feb» en mayúscula, y la entrada de identidad se
    # las pasaba a minúscula. Una traducción que no cambia nada no es inofensiva.
    "ene": "jan", "abr": "apr", "ago": "aug", "dic": "dec",
    "cada casilla es un día y cuanto más clara más saltó la alarma; el aspa es un día que no existe":
        "each cell is a day, the lighter the more the alarm fired;\nthe cross is a day that does not exist",

    # --- módulo 9, tipos y decisiones ----------------------------------
    "corriente del motor, en amperios (los cortes en trazo discontinuo)":
        "motor current, in amperes (the cuts dashed)",
    "corriente del motor, A": "motor current, A",
    "en vacio\n30,1 %": "unloaded\n30.1%",
    "en carga\n15,2 %": "loaded\n15.2%",
    "la ficha dice 7 A en carga": "the datasheet says 7 A loaded",
    "presión TP2, bar": "pressure TP2, bar",
    "lecturas": "readings",
    "lo que encuentra  TP2 = 8.2:\n107 lecturas, esta raya":
        "what TP2 = 8.2 finds:\n107 readings, this line",
    "8,2 bar: el umbral de arranque": "8.2 bar: the start threshold",

    # --- módulo 12, juntar tablas --------------------------------------
    "filas que devuelve el cruce (escala logarítmica)": "rows the join returns (log scale)",
    "6 filas al cruzar por  nr": "6 rows when joining on  nr",

    # --- módulo 13, ventanas -------------------------------------------
    "2020-06-05, de 08:00 a 10:00": "2020-06-05, from 08:00 to 10:00",
    "cada línea es un arranque: 6 en estas dos horas":
        "each line is a start: 6 in these two hours",
    "en carga": "loaded",
    "en vacío": "unloaded",

    # --- módulo 14, la plata -------------------------------------------
    "casillas de diez segundos": "ten second slots",
    "casillas con lectura": "slots with a reading",
    "casilla con lectura": "slot with a reading",
    "casilla vacía: 90 de 241": "empty slot: 90 of 241",
    "huecos": "holes",
    "2020-06-12, cuarenta minutos con el compresor ciclando":
        "2020-06-12, forty minutes of the compressor cycling",
    "presión del panel, bar": "panel pressure, bar",
    "TP3, bar": "TP3, bar",

    # --- módulo 15, las otras fuentes ----------------------------------
    "clima: 24 puntos, uno cada hora": "weather: 24 points, one every hour",
    "averías: 1 suceso en todo el día": "failures: 1 event in the whole day",
    "2020-06-05, el día que empieza la avería #3":
        "2020-06-05, the day failure #3 begins",
    "aceite, °C": "oil, °C",
    "calle, °C": "street, °C",
    "parte #3": "report #3",

    # --- módulo 16, el contrato ----------------------------------------
    #
    # Los nombres de las promesas y de las roturas son frases, no
    # identificadores, así que aquí sí se traducen. En el bloque `salida` de la
    # lección siguen en español en las dos ediciones, porque eso es una
    # transcripción literal de lo que el programa imprime.
    "la rotura que llega el lunes; encendido, la promesa que se entera":
        "the breakage that arrives on Monday; lit, the promise that notices",
    "las columnas son las acordadas": "the columns are the agreed ones",
    "no llegan columnas de mas": "no extra columns arrive",
    "timestamp no se repite": "timestamp does not repeat",
    "la presion esta en bar y no en otra unidad": "pressure is in bar and no other unit",
    "las digitales solo valen cero o uno": "the digitals are only ever zero or one",
    "el recuento de lecturas nunca es negativo": "the reading count is never negative",
    "el dia se corresponde con la marca de tiempo": "the day matches the timestamp",
    "una casilla sin medir no trae presion": "an unmeasured slot carries no pressure",
    "columna\nrenombrada": "renamed\ncolumn",
    "otra\nunidad": "another\nunit",
    "columna\nnueva": "new\ncolumn",
    "ingesta\nrepetida": "repeated\ningestion",
    "valor\nimposible": "impossible\nvalue",

    # --- módulo 17, el linaje de dbt -----------------------------------
    "el lago": "the lake",
    "preparación": "preparation",
    # La tercera columna del grafo. Se escondía tras el corte de longitud, y la
    # cazó bajarlo a 3: es el nombre de una capa, no un identificador.
    "oro": "gold",

    # --- módulo 18, el viaje en el tiempo ------------------------------
    "versión 0, la plata con el fallo": "version 0, the buggy silver",
    "versión 1, la plata arreglada": "version 1, the fixed silver",
    "las líneas verticales son las cuatro averías":
        "the vertical lines are the four failures",
    "horas de carga al día": "loaded hours per day",
    "horas en carga": "hours loaded",
    "día con parte de avería": "day with a failure report",
    "media 3.42 h": "mean 3.42 h",
    "escribir las dos versiones": "writing both versions",
    "leer la última versión": "reading the latest version",
    "leer la versión vieja": "reading the old version",
    "leer preguntando primero": "reading after asking first",
    "segundos, mediana de siete corridas y su rango":
        "seconds, median of seven runs and its range",

    # --- módulo 19, fichero contra servicio ----------------------------
    "un fichero": "a file",
    "un servicio": "a service",
    "los rangos se pisan: no se distinguen": "the ranges overlap: they do not differ",
    "segundos en responder la misma pregunta": "seconds to answer the same question",
    "MB que ocupan las mismas lecturas": "MB the same readings take",

    # --- módulo 20, el esquema como contrato ---------------------------
    "clave primaria": "primary key",
    "clave foránea": "foreign key",
    "no vacío": "not null",
    "condición": "check",
    "la guarda que el motor impone, leída de su propio catálogo":
        "the guard the engine enforces, read from its own catalogue",
}

# Etiquetas construidas con f-strings: llevan un número dentro, así que no se
# pueden buscar como literales. El patrón casa el español normalizado y el
# reemplazo lo reconstruye en inglés.
PATTERNS: list[tuple[str, str]] = [
    # Las etiquetas del cruce del módulo 12: número de parte y fecha de inicio.
    # Van por patrón y no una a una porque los cuatro partes salen de un fichero,
    # y si mañana se corrigiera una fecha la figura inglesa seguiría al día.
    (r"^#(\d+) con (\d{4}-\d{2}-\d{2})$", r"#\1 with \2"),
    # Los tamaños del módulo 5, que se recalculan en cada corrida.
    (r"^([\d.]+) m$", r"\1 M"),
    (r"^(\d+) veces$", r"\1 times"),

    # Las etiquetas que llevan una cifra medida dentro. Van por patrón y no una a
    # una a propósito: `es()` ya devuelve el número en inglés, así que fijarlo en
    # la clave lo dejaría caducado en cuanto la medida cambiara. El número viaja
    # desde la figura y aquí solo se traducen las palabras de alrededor.
    #
    # Las dobles espacios de la alineación se pierden al normalizar la clave, y
    # por eso se vuelven a escribir en el reemplazo.
    (r"^mediana, ([\d,]+)$", r"median, \1"),
    (r"^un dia lleno, ([\d,]+) lecturas$", r"a full day, \1 readings"),
    (r"^telemetria: ([\d,]+) puntos, uno cada 10 s$",
     r"telemetry: \1 points, one every 10 s"),
    (r"^parado ([\d.]+) %$", "stopped\n" + r"\1%"),
    (r"^en vacio ([\d.]+) %$", "unloaded\n" + r"\1%"),
    (r"^en carga ([\d.]+) %$", "loaded\n" + r"\1%"),
    (r"^lo que querias decir: toda esta banda, ([\d,]+) lecturas$",
     r"what you meant: this whole band, \1 readings"),
    (r"^las ([\d,]+) lecturas de partida$", r"the \1 we started with"),
    (r"^([\d,]+) todas las lecturas, con averia o sin ella$",
     r"\1   every reading,  failure or no failure"),
    (r"^([\d,]+) solo las lecturas con averia$",
     r"\1   only readings  during a failure"),
    (r"^([\d,]+) cada lectura con cada parte$",
     r"\1   every reading x  every report"),
    (r"^([\d.]+) veces mas disco$", r"\1 times more disk"),
]

TABLE: dict[str, str] = {}

# Nombres que matplotlib da a sus propios artistas y nunca enseña a nadie.
INTERNAL_PREFIXES = ("_nolegend_", "_child", "_collection", "_line", "_container", "_axes")

_already_english: set[str] = set()
_missing: set[str] = set()
_written: list[str] = []
_installed = False


def language() -> str:
    """En qué idioma se dibuja. Español salvo que FIG_LANG diga otra cosa."""
    return os.environ.get("FIG_LANG", "es").lower()


def sufijo() -> str:
    """Lo que se cuela en el nombre del fichero: nada en español, `.en` en inglés."""
    return "" if language() == "es" else f".{language()}"


def destino(path: Path | str) -> Path:
    """El fichero que de verdad se escribe para el idioma en curso.

    `figures_theme` la usa para calcular la huella del fichero correcto: durante
    una corrida inglesa, `fig_x.claro.png` existe (es el español) y leerlo daría
    una huella que no corresponde con lo que se acaba de escribir.
    """
    path = Path(path)
    marca = sufijo()
    if not marca or path.suffixes[:1] == [marca]:
        return path
    return path.with_name(path.stem + marca + path.suffix)


def normalise(text: str) -> str:
    """Sin acentos, sin mayúsculas y sin saltos, para que case como se escriba."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.lower().split())


def looks_translatable(text: str) -> bool:
    """Si la cadena es prosa que merece reportarse, y no un número o una unidad."""
    key = normalise(text)
    if any(re.fullmatch(p, key) for p in NEUTRAL_PATTERNS):
        return False
    # El corte estaba en 4 y por eso «abr» y «ago» del eje del módulo 8 nunca se
    # reportaron: una palabra española corta se colaba en la figura inglesa sin
    # que la puerta dijera nada. Con 3, los meses salen y el ruido sigue fuera
    # porque los números y las unidades los filtra NEUTRAL_PATTERNS.
    if key in NEUTRAL or text.startswith(INTERNAL_PREFIXES) or len(key) < 3:
        return False
    if key in _already_english:
        return False
    return any(c.isalpha() for c in key) and not key.replace(".", "").replace(",", "").isdigit()


def translate(text: str) -> str:
    """El inglés de una etiqueta española, recordando las que no lo tienen."""
    if not isinstance(text, str) or not text.strip():
        return text
    key = normalise(text)
    if key in TABLE:
        return TABLE[key]
    for pattern, replacement in PATTERNS:
        if re.fullmatch(pattern, key):
            english = re.sub(pattern, replacement, key)
            # Se recuerda: matplotlib fija algunas etiquetas dos veces, y la
            # segunda pasada reportaría nuestro propio inglés como sin traducir.
            _already_english.add(" ".join(english.lower().split()))
            return english
    if looks_translatable(text):
        _missing.add(text)
    return text


def install() -> None:
    """Parchea los puntos por los que pasa todo texto visible y todo fichero.

    Idempotente, y no hace nada en español, así que un script puede llamarla sin
    condiciones. Importar pyplot ANTES: pyplot copia la firma de `Figure.savefig`
    al importarse y rechaza una parcheada que no reconoce.
    """
    global _installed
    if _installed or language() == "es":
        return

    from matplotlib.artist import Artist
    from matplotlib.figure import Figure
    from matplotlib.text import Text

    original_set_text = Text.set_text
    original_set_label = Artist.set_label
    original_savefig = Figure.savefig

    def set_text(self, s):
        return original_set_text(self, translate(s) if isinstance(s, str) else s)

    def set_label(self, s):
        return original_set_label(self, translate(s) if isinstance(s, str) else s)

    def savefig(self, fname, *args, **kwargs):
        """Escribe fig_x.claro.en.png, para no pisar la figura española."""
        if isinstance(fname, (str, os.PathLike)):
            fname = destino(fname)
            _written.append(Path(fname).name)
        return original_savefig(self, fname, *args, **kwargs)

    Text.set_text = set_text
    Artist.set_label = set_label
    Figure.savefig = savefig
    _installed = True

    # Cada script de figuras corre en su propio proceso, así que lo que encuentre
    # tiene que salir de ahí escrito. El runner junta los informes.
    if os.environ.get("FIG_I18N_REPORT"):
        import atexit

        atexit.register(volcar_informe)


def volcar_informe() -> None:
    """Deja lo que esta corrida escribió y lo que no supo traducir."""
    destino_json = os.environ.get("FIG_I18N_REPORT")
    if not destino_json:
        return
    import json

    with open(destino_json, "w", encoding="utf-8") as fh:
        json.dump({"escritas": _written, "sin_traducir": sorted(_missing)},
                  fh, ensure_ascii=False, indent=2)


def missing() -> set[str]:
    """Toda cadena visible que esta corrida encontró sin traducción."""
    return set(_missing)


def written() -> list[str]:
    """Las figuras escritas en esta corrida, en el orden en que se dibujaron."""
    return list(_written)


def _construir_tabla() -> None:
    """Normaliza las claves de `TRADUCCIONES` una sola vez, al importar.

    Así el diccionario de arriba se escribe con acentos y mayúsculas, como se lee,
    y aun así casa con lo que matplotlib pinta, que puede venir de un f-string.
    """
    for es, en in TRADUCCIONES.items():
        TABLE[normalise(es)] = en
        # Nuestro propio inglés, para que una etiqueta que matplotlib fija dos
        # veces no se reporte como española en la segunda pasada.
        _already_english.add(" ".join(en.lower().split()))


_construir_tabla()
