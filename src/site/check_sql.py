"""Cada consulta publicada se ejecuta de verdad, y su salida dice la verdad.

Es la puerta más importante de este curso. Enseña SQL: publicar una consulta que
no corre, o una salida que la consulta no produce, sería el peor fallo posible, y
es justo el que no se ve releyendo. Una consulta rota se lee estupendamente.

Comprueba tres cosas, de menos a más exigente:

  1. **La consulta corre.** Cada bloque `sql` y `sql-vivo` se ejecuta contra el
     lago de verdad. Si da error de sintaxis o de columna, falla aquí.
  2. **La salida no miente.** Si al bloque le sigue un `salida` con números, cada
     uno de esos números tiene que aparecer en el resultado real. No se compara
     el texto entero, porque las salidas llevan cabeceras y alineación a mano,
     pero un número inventado no sobrevive.
  3. **La solución del reto resuelve el reto.** Se ejecuta y se compara con la
     respuesta guardada en `results/retos.json`, la misma contra la que la página
     corrige al lector. Si la solución publicada no da la respuesta esperada, el
     reto es una trampa.

Correr:  .venv\\Scripts\\python.exe src\\site\\check_sql.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
LESSONS = PROJECT / "lecciones"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
SAMPLES = PROJECT / "assets" / "muestras"
RETOS = PROJECT / "results" / "retos.json"

NUMBER = re.compile(r"-?\d[\d.,]*\d|\d")


def bloques(text: str) -> list[tuple[int, str, str]]:
    """Los bloques cercados: (línea donde abre, lenguaje, contenido)."""
    out, actual, lang, inicio = [], [], None, 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            if lang is None:
                lang, inicio, actual = line[3:].strip(), n, []
            else:
                out.append((inicio, lang, "\n".join(actual)))
                lang = None
        elif lang is not None:
            actual.append(line)
    return out


def normaliza(valor) -> str:
    if isinstance(valor, float):
        return f"{valor:.10g}"
    if hasattr(valor, "isoformat"):
        return valor.isoformat()[:10]
    return str(valor)


# Una fecha ISO no es tres números: es una fecha. Sin quitarlas antes, el 18 de
# «2020-04-18» se leía como el número negativo -18 y la salida parecía inventarse
# cifras que nadie había escrito.
FECHA = re.compile(r"\d{4}-\d{2}(-\d{2})?")


def solo_datos(texto: str) -> str:
    """Las filas de datos de una caja de DuckDB, sin su cabecera.

    La cabecera lleva el nombre de cada columna y su tipo, y ahí hay números que
    no son datos: `avg(TP2)` trae un 2 e `int128` trae un 128. Contándolos, la
    puerta acusaba a la lección de publicar cifras que la consulta no devuelve,
    cuando lo único que pasaba es que una columna se llama TP2.

    Solo recorta si encuentra la línea que separa cabecera de datos. Una salida
    que no sea una caja de DuckDB se mira entera, como antes.
    """
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if linea.lstrip().startswith("├"):
            return "\n".join(lineas[i + 1:])
    return texto


def numeros_de(texto: str) -> set:
    """Los números de una salida, sin separadores de millares ni fechas."""
    out = set()
    texto = FECHA.sub(" ", solo_datos(texto))
    for m in NUMBER.finditer(texto):
        # Un dígito pegado a letras no es un número publicado: es parte de un
        # nombre. Las señales de este compresor se llaman TP2, TP3, H1 y LPS, y
        # sin esto la puerta leía el 3 de «TP3» como una cifra que la consulta
        # no devuelve, cuando lo que devuelve es el texto «TP3» entero.
        antes = texto[m.start() - 1] if m.start() else " "
        despues = texto[m.end()] if m.end() < len(texto) else " "
        if antes.isalpha() or despues.isalpha() or antes == "_" or despues == "_":
            continue
        crudo = m.group().rstrip(".,")
        limpio = crudo.replace(",", "") if re.fullmatch(r"-?\d{1,3}(,\d{3})+", crudo) else crudo
        try:
            valor = float(limpio)
        except ValueError:
            continue
        out.add(f"{valor:.10g}")
    return out


def conectar():
    con = duckdb.connect()
    if BRONZE.exists():
        con.execute(
            f"CREATE VIEW telemetria AS "
            f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
        )
        con.execute(f"CREATE VIEW t AS SELECT * FROM telemetria")
    # La capa de plata, si existe. Desde el módulo 14 las lecciones consultan
    # `plata` igual que consultaban `telemetria`, y sin registrarla aquí sus
    # consultas publicadas no se podrían ejecutar.
    if SILVER.exists():
        con.execute(f"CREATE VIEW plata AS "
                    f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")
    # Las tablas pequeñas que acompañan a la telemetría, como los partes de
    # avería del módulo 12. Del lago no salen: son de `assets/muestras/`, que es
    # también de donde las coge el navegador.
    for extra in sorted(SAMPLES.glob("*.parquet")):
        if extra.stem in ("averias", "clima", "horas"):
            con.execute(f"CREATE VIEW {extra.stem} AS "
                        f"SELECT * FROM read_parquet('{extra.as_posix()}')")
    return con


def revisa(path: Path, con, respuestas: dict) -> list[str]:
    # El nombre lleva el idioma: las dos ediciones comparten fichero y un
    # mensaje sin idioma manda a buscar el fallo al sitio equivocado.
    nombre = path.name + (" (en)" if path.parent.name == "en" else "")
    text = io.open(path, encoding="utf-8").read()
    trozos = bloques(text)
    problemas = []

    for i, (linea, lang, cuerpo) in enumerate(trozos):
        if lang in ("sql", "sql-vivo"):
            sql = cuerpo.strip().rstrip(";")
            if not sql.lower().lstrip().startswith(("select", "with")):
                continue
            try:
                filas = con.sql(sql).fetchall()
            except Exception as e:
                problemas.append(f"{nombre}:{linea}  la consulta NO CORRE: "
                                 f"{str(e).splitlines()[0][:90]}")
                continue

            # La salida que la sigue, si la hay, no puede inventarse números.
            #
            # Se salta el bloque `anota`, que casi siempre va en medio. Mirar solo
            # el bloque inmediatamente siguiente hacía que esta comprobación no se
            # ejecutara nunca en las lecciones reales, y el verificador daba verde
            # sin haber mirado nada.
            siguiente = None
            for j in range(i + 1, min(i + 3, len(trozos))):
                if trozos[j][1] == "salida":
                    siguiente = trozos[j]
                    break
                if trozos[j][1] not in ("anota",):
                    break
            if not siguiente:
                continue

            reales = set()
            for fila in filas:
                for v in fila:
                    reales.add(normaliza(v))
                    # Un valor de texto puede llevar números dentro, y son suyos.
                    # Las fechas de los partes de avería llegan como texto,
                    # «4/18/2020 0:00», y la puerta acusaba a la lección de
                    # publicar un 0 y un 18 que la consulta sí devuelve, solo que
                    # dentro de una cadena.
                    if isinstance(v, str):
                        reales |= numeros_de(v)
                    # Y una marca de tiempo lleva su hora dentro. `normaliza` se
                    # queda solo con la fecha, así que el 10 de «00:00:10» no
                    # entraba y la puerta lo daba por inventado.
                    elif hasattr(v, "isoformat"):
                        reales |= numeros_de(v.isoformat()[11:])
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        # La salida publicada suele venir redondeada, así que un
                        # 23,81 tiene que casar con un 23,808333 del resultado.
                        for dec in range(0, 5):
                            reales.add(f"{round(float(v), dec):.10g}")
            publicados = numeros_de(siguiente[2])
            faltan = {p for p in publicados if p not in reales}
            # Los números de la cabecera y de la alineación no son datos: se
            # tolera que un valor publicado no aparezca si la consulta devolvió
            # texto o fechas en esa posición. Lo que se persigue es el número
            # que nadie midió.
            if faltan and filas:
                muestra = ", ".join(sorted(faltan)[:4])
                problemas.append(
                    f"{nombre}:{siguiente[0]}  la salida publica números que la consulta "
                    f"no devuelve: {muestra}")

        elif lang == "reto":
            campos, actual = {}, None
            for line in cuerpo.splitlines():
                head, sep, rest = line.partition(":")
                if sep and head.strip() in ("pregunta", "inicio", "esperado", "pista", "solucion"):
                    actual = head.strip()
                    campos[actual] = [rest.strip()] if rest.strip() else []
                elif actual:
                    campos[actual].append(line.rstrip())
            solucion = "\n".join(campos.get("solucion", [])).strip().rstrip(";")
            clave = "\n".join(campos.get("esperado", [])).strip()
            if not solucion or not clave:
                continue
            if clave not in respuestas:
                problemas.append(f"{nombre}:{linea}  el reto pide «{clave}» y no está en "
                                 f"results/retos.json")
                continue
            try:
                filas = con.sql(solucion).fetchall()
            except Exception as e:
                problemas.append(f"{nombre}:{linea}  la SOLUCIÓN del reto no corre: "
                                 f"{str(e).splitlines()[0][:80]}")
                continue
            esperadas = respuestas[clave]["rows"]
            obtenidas = [[normaliza(v) for v in fila] for fila in filas]
            esperadas_n = [[normaliza(v) for v in fila] for fila in esperadas]
            if sorted(obtenidas) != sorted(esperadas_n):
                problemas.append(
                    f"{nombre}:{linea}  la solución publicada NO da la respuesta esperada: "
                    f"{len(obtenidas)} filas contra {len(esperadas_n)}")

    return problemas


# Las lecciones consultan ficheros que no crea `bronze.py`, sino los scripts de
# su propio módulo. Sin esta lista, una reconstrucción desde cero fallaba con un
# «No files found» que no dice a quién hay que llamar.
DEPENDE_DE = {
    PROJECT / "lake" / "_formatos" / "todo.parquet":
        "src/transform/benchmark_formats.py  (lo usan las consultas del módulo 7)",
    SILVER: "src/transform/silver.py  (la consultan las lecciones desde el módulo 14)",
}


def main() -> None:
    if not BRONZE.exists():
        print("  no hay lago todavía: nada que ejecutar")
        return

    faltan = [f"{ruta.relative_to(PROJECT)}  ->  corre {quien}"
              for ruta, quien in DEPENDE_DE.items() if not ruta.exists()]
    if faltan:
        print("  faltan ficheros que las lecciones consultan:")
        for f in faltan:
            print(f"    {f}")
        raise SystemExit("El lago está incompleto. No se puede verificar el SQL publicado.")

    respuestas = json.loads(io.open(RETOS, encoding="utf-8").read()) if RETOS.exists() else {}
    con = conectar()

    lecciones = sorted(LESSONS.glob("m[0-9][0-9]_*.md"))
    lecciones += sorted((LESSONS / "en").glob("m[0-9][0-9]_*.md"))

    problemas, consultas = [], 0
    for path in lecciones:
        encontrados = revisa(path, con, respuestas)
        consultas += sum(1 for _, lang, _ in bloques(io.open(path, encoding="utf-8").read())
                         if lang in ("sql", "sql-vivo"))
        etiqueta = path.stem + (" (en)" if path.parent.name == "en" else "")
        print(f"  {etiqueta:<26} {'verde' if not encontrados else f'{len(encontrados)} problemas'}")
        problemas += encontrados

    print()
    print(f"  {consultas} bloques de SQL ejecutados contra el lago")
    if problemas:
        for p in problemas:
            print(f"  {p}")
        raise SystemExit(f"{len(problemas)} problemas de SQL. No commitear.")
    print("Todas las consultas publicadas corren y dicen la verdad.")


if __name__ == "__main__":
    main()
