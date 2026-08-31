"""Types, and the rule that turns a current into a state. Module 9.

Two things, and the second is the module's product:

  1. **8.2 is not 8.2.** Asking for a decimal with the equals sign finds far
     fewer rows than the reader means, and the trap is that it finds SOME. A
     query returning nothing looks broken; a query returning 2% of the truth
     looks fine.

  2. **Three states from one column.** The datasheet says the motor draws about
     0 A stopped, 4 A offloaded and 7 A loaded. That is a claim, and the
     thresholds it implies are the kind of knob this project refuses to copy
     from a document. They get chosen by looking at the distribution, and then
     checked against a signal that was not used to build them.

That check is what makes the rule more than an opinion. `DV_eletric` marks load
independently of the current, so if the thresholds are right, nearly every
reading above the loaded threshold should carry it.

Run:  .venv\\Scripts\\python.exe src\\transform\\queries_m09.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT / "assets" / "muestras" / "sql.parquet"
RESULTS = PROJECT / "results" / "m09_tipos.json"

# El umbral del presostato que declara la ficha del dataset.
UMBRAL = 8.2

# Los dos cortes de la regla, elegidos mirando la distribución y no la ficha.
PARADO, CARGA = 1.0, 5.0


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("Falta la muestra. Corre src/site/make_sample.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")
    filas = con.sql("SELECT count(*) FROM t").fetchone()[0]

    # --- 1. El igual y los decimales -------------------------------------
    exacto = con.sql(f"SELECT count(*) FROM t WHERE TP2 = {UMBRAL}").fetchone()[0]
    # Dos formas de decir «8,2», y las dos encuentran mucho más que el igual.
    # La primera es la honesta: lo que una pantalla de dos decimales ENSEÑA como
    # 8,20. La segunda es «alrededor de 8,2», con un decimal.
    en_pantalla = con.sql(
        f"SELECT count(*) FROM t WHERE round(TP2, 2) = {UMBRAL}").fetchone()[0]
    redondeando = con.sql(
        f"SELECT count(*) FROM t WHERE round(TP2, 1) = {UMBRAL}").fetchone()[0]
    # Los valores de verdad que una pantalla de dos decimales confunde con 8,20.
    # Aquí no hay ruido binario: el sensor da tres decimales y la pantalla se
    # come el tercero. Esa es la razón real de que el igual falle en este
    # fichero, y es más común que la de la coma flotante.
    vecinos = con.sql(f"""
        SELECT DISTINCT TP2 FROM t
        WHERE round(TP2, 2) = {UMBRAL} AND TP2 <> {UMBRAL}
        ORDER BY abs(TP2 - {UMBRAL}) LIMIT 4
    """).fetchall()
    # Y la trampa en su forma más corta, con una sorpresa: en DuckDB el ejemplo
    # clásico NO falla. Un literal como 0.1 es DECIMAL, que es exacto, así que
    # 0.1 + 0.2 = 0.3 sale cierto. El fallo aparece solo al elegir el tipo coma
    # flotante, que es justo el tipo que tiene TP2. El módulo va de eso: manda
    # el tipo, no el número.
    decimal_igual, decimal_suma, double_igual, double_suma, tipo_literal = con.sql("""
        SELECT 0.1 + 0.2 = 0.3                            AS decimal_igual,
               (0.1 + 0.2)::VARCHAR                       AS decimal_suma,
               0.1::DOUBLE + 0.2::DOUBLE = 0.3::DOUBLE    AS double_igual,
               (0.1::DOUBLE + 0.2::DOUBLE)::VARCHAR       AS double_suma,
               typeof(0.1)                                AS tipo_literal
    """).fetchone()
    tipo_tp2 = con.sql("SELECT typeof(TP2) FROM t LIMIT 1").fetchone()[0]

    # --- 2. Los tres estados ---------------------------------------------
    regla = f"""
        CASE WHEN Motor_current < {PARADO} THEN 'parado'
             WHEN Motor_current < {CARGA}  THEN 'en vacio'
             ELSE 'en carga' END
    """
    estados = con.sql(f"""
        SELECT {regla} AS estado,
               count(*) AS lecturas,
               round(count(*) * 100.0 / (SELECT count(*) FROM t), 1) AS por_ciento,
               round(count(*) * 10 / 3600.0, 1) AS horas,
               round(avg(Motor_current), 2) AS corriente_media,
               round(avg(DV_eletric) * 100, 1) AS por_ciento_marcado_en_carga
        FROM t
        GROUP BY estado
        ORDER BY corriente_media
    """).fetchall()

    # DuckDB devuelve Decimal en los round() y JSON no sabe escribirlo.
    por_estado = [{"estado": e, "lecturas": n, "por_ciento": float(p), "horas": float(h),
                   "corriente_media": float(c), "por_ciento_marcado_en_carga": float(d)}
                  for e, n, p, h, c, d in estados]
    carga = next(x for x in por_estado if x["estado"] == "en carga")

    # Lo que dice la ficha contra lo que hace el fichero.
    moda_en_carga = con.sql(f"""
        SELECT round(Motor_current * 2) / 2 AS amperios, count(*) AS lecturas
        FROM t WHERE Motor_current >= {CARGA}
        GROUP BY amperios ORDER BY lecturas DESC LIMIT 1
    """).fetchone()

    payload = {
        "filas": filas,
        "umbral_de_la_ficha": UMBRAL,
        "filas_con_igual_exacto": exacto,
        "filas_como_se_ven_en_pantalla": en_pantalla,
        "filas_redondeando": redondeando,
        "por_ciento_que_encuentra_el_igual_en_pantalla": round(exacto * 100 / en_pantalla, 1),
        "veces_que_se_pierde": round(redondeando / exacto, 1) if exacto else None,
        "por_ciento_que_encuentra_el_igual": round(exacto * 100 / redondeando, 1),
        "vecinos_del_umbral": [v[0] for v in vecinos],
        "decimal_es_exacto": bool(decimal_igual),
        "decimal_suma": decimal_suma,
        "double_es_exacto": bool(double_igual),
        "double_suma": double_suma,
        "tipo_de_un_literal": tipo_literal,
        "tipo_de_TP2": tipo_tp2,
        "corte_parado": PARADO,
        "corte_carga": CARGA,
        "estados": por_estado,
        "por_ciento_en_carga": carga["por_ciento"],
        "acuerdo_con_dv_eletric": carga["por_ciento_marcado_en_carga"],
        "amperios_mas_frecuentes_en_carga": float(moda_en_carga[0]),
        "amperios_que_dice_la_ficha_en_carga": 7,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  pedir TP2 = {UMBRAL} encuentra {exacto:,} filas")
    print(f"  en una pantalla de dos decimales se ven como {UMBRAL:.2f}: {en_pantalla:,}")
    print(f"  pedir round(TP2,1) = {UMBRAL} encuentra {redondeando:,}")
    print(f"  el igual encuentra el {payload['por_ciento_que_encuentra_el_igual']} % "
          f"de lo que el lector quería")
    print(f"  ahí dentro hay valores como: "
          f"{', '.join(str(v[0]) for v in vecinos[:3])}")
    print(f"  un literal como 0.1 es {tipo_literal} y la columna TP2 es {tipo_tp2}")
    print(f"    en {tipo_literal}: 0.1 + 0.2 = {decimal_suma}, y comparado con 0.3 da {decimal_igual}")
    print(f"    en DOUBLE:  0.1 + 0.2 = {double_suma}, y comparado con 0.3 da {double_igual}")
    print()
    print("  estado      lecturas   %      horas   corriente   marcado en carga")
    for x in por_estado:
        print(f"  {x['estado']:<11} {x['lecturas']:>8,} {x['por_ciento']:>5} "
              f"{x['horas']:>9} {x['corriente_media']:>10} "
              f"{x['por_ciento_marcado_en_carga']:>15}")
    print()
    print(f"  en carga, lo más frecuente son {moda_en_carga[0]} A "
          f"y la ficha dice 7 A")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # La regla no vale si una señal independiente no la respalda.
    if carga["por_ciento_marcado_en_carga"] < 90:
        raise SystemExit("DV_eletric no respalda el corte de carga. La regla no vale.")
    if exacto >= redondeando:
        raise SystemExit("El igual exacto no pierde filas. El módulo no tiene caso.")
    if not decimal_igual or double_igual:
        raise SystemExit("Los dos tipos no se comportan como dice la lección. "
                         "Si esto cambia, la lección hay que reescribirla.")


if __name__ == "__main__":
    main()
