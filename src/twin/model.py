"""The compressor's physics, and the only place it lives. Module 24.

A receiver that fills and empties, a pressure switch with hysteresis, and
nothing else. Four numbers describe it, and **none of them is invented**: all
four get measured from the lake here, and the datasheet gets contradicted where
it deserves to be.

  - the pressure that starts the compressor loading
  - the pressure that stops it
  - how fast the receiver fills while loaded
  - how fast it empties, which is what the plant is consuming

The fourth is the interesting one. Measured as an instantaneous slope over one
ten second step it comes out **a third below the truth**, and the reason is not
the instrument: the smallest move TP3 ever makes is 0.001 bar, measured here
rather than assumed, which is fine enough to see it. The reason is that the plant does not
breathe evenly. Air goes in bursts, so most ten second steps are quieter than
average and the median lands below the mean. Estimating it over a whole unloaded
stretch instead, pressure drop divided by duration, averages that away.

An earlier version of this file claimed the median sat exactly on the sensor's
resolution, which it did, at 0.060 bar/min against an assumed 0.01 bar step. The
step is five times finer than that, so the coincidence meant nothing.

Run:  .venv\\Scripts\\python.exe src\\twin\\model.py
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m24_fisica.json"

# La ventana sana con la que se calibra. **Febrero entero, y solo febrero.**
#
# Iba hasta el 15 de marzo, elegida por fecha (antes de la primera avería
# documentada, la del 18 de abril) para no estar escogiendo los datos que
# confirman el modelo. Al calibrar en el módulo 26 se vio que no cuadraba, y la
# razón es que **del 1 al 12 de marzo la máquina está averiada y nadie lo
# documentó**: la carga pasa de 0,06 a 0,58, el aceite sube diez grados, la
# corriente dobla y el 11 salta la alarma de baja presión por primera vez en
# todo el registro. El 13 vuelve todo a lo de antes.
#
# Así que la ventana de calibración llevaba doce días de avería dentro. Elegir
# por fecha protege de escoger a conveniencia, pero no de esto: hay que mirar.
SANO = ("2020-02-01", "2020-02-29")

# Y el evento que se encontró, que el curso publica como hallazgo.
MARZO = ("2020-03-01", "2020-03-12")

# Lo que promete la ficha del dataset, para poder contrastarlo.
FICHA_ARRANQUE = 8.2
FICHA_ALARMA = 7.0

# Un tramo de menos de dos minutos no sirve para estimar una pendiente: la
# resolución del sensor se come la señal.
TRAMO_MINIMO_S = 120

# El registro va a una lectura cada diez segundos. Por encima de quince ya no es
# jitter, es un hueco: hay 35 de más de una hora solo en la ventana sana, casi
# todos de madrugada, cuando el metro no circula. Lo que pasó dentro no se sabe.
SALTO_MAXIMO = 15


@dataclass(frozen=True)
class Deposito:
    """Los cuatro números que describen la máquina, en bar y en bar por minuto."""

    arranca: float          # presión a la que el presostato pide carga
    para: float             # presión a la que la suelta
    llena: float            # subida mientras carga, ya descontado el consumo
    consumo: float          # bajada en vacío, o sea lo que la planta gasta

    @property
    def entrega(self) -> float:
        """Lo que mete el compresor, que es lo que sube más lo que se gasta."""
        return self.llena + self.consumo

    @property
    def banda(self) -> float:
        return self.para - self.arranca


def _lago() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"CREATE VIEW p AS SELECT * FROM "
                f"read_parquet('{SILVER.as_posix()}/**/*.parquet') WHERE medido")
    return con


def conmutacion(con, desde: str, hasta: str) -> tuple[float, float]:
    """Las dos presiones a las que el presostato cambia de idea."""
    filas = con.sql(f"""
        WITH t AS (
          SELECT TP3, DV_eletric, lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
          FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        )
        SELECT DV_eletric, median(TP3)
        FROM t WHERE antes IS NOT NULL AND antes <> DV_eletric
        GROUP BY DV_eletric
    """).fetchall()
    mapa = {int(dv): float(v) for dv, v in filas}
    return mapa[1], mapa[0]


def _crea_tramos(con, desde: str, hasta: str) -> None:
    """Parte el registro en tramos: cada carga y cada vacío, de punta a punta.

    **Sin filtrar por duración**, y eso importa. El primer intento se quedaba solo
    con los tramos de dos minutos o más, y como las cargas duran 1,8 min de
    mediana y los vacíos 22, el filtro tiraba casi todas las cargas y ninguno de
    los vacíos. El balance de aire salía descuadrado por un factor de 2,3 y la
    culpa era del filtro, no de la máquina.

    Y hay un segundo tropiezo, encontrado al calibrar en el módulo 26. La
    duración se sacaba con `date_diff` de la primera lectura a la última, y el
    registro **tiene huecos**: 35 de más de una hora en esta ventana, casi todos
    de madrugada. Un tramo que salta un hueco se lleva las horas del hueco como
    si el compresor las hubiera trabajado, y eso hunde la velocidad medida.

    Así que cada tramo lleva ahora dos cosas más: los minutos contados por
    intervalos de verdad, y una marca de si dentro hay un hueco. Lo que pasó
    dentro del hueco no se sabe, así que esos tramos no miden nada.
    """
    con.execute(f"""
        CREATE OR REPLACE VIEW tramos AS
        WITH t AS (
          SELECT timestamp, day, TP3, DV_eletric,
                 lag(DV_eletric) OVER (ORDER BY timestamp) AS antes,
                 date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                           timestamp) AS salto
          FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        ), marcados AS (
          SELECT *, sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
                        OVER (ORDER BY timestamp) AS tramo
          FROM t
        )
        SELECT any_value(DV_eletric) AS cargando,
               any_value(day) AS day,
               count(*) AS lecturas,
               (count(*) - 1) / 6.0 AS minutos,
               date_diff('second', min(timestamp), max(timestamp)) / 60.0 AS span,
               max(CASE WHEN salto > {SALTO_MAXIMO} THEN 1 ELSE 0 END) AS roto,
               first(TP3 ORDER BY timestamp) AS p_ini,
               last(TP3 ORDER BY timestamp) AS p_fin
        FROM marcados GROUP BY tramo
    """)


def balance(con) -> dict:
    """El aire que entra contra el que sale, y lo que eso da de sí.

    Es la comprobación que manda. Sobre seis semanas la presión acaba donde
    empezó, así que **los bar metidos tienen que igualar a los gastados**. Si no
    cuadran, lo que está mal es la medida y no hay modelo que valga.

    Y de aquí salen los dos parámetros, promediados por minuto y no por lectura:
    para un ciclo de trabajo lo que cuenta es cuánto aire se mueve en total, no
    la pendiente típica de un instante.
    """
    fila = con.sql("""
        SELECT sum(CASE WHEN cargando = 1 THEN p_fin - p_ini ELSE 0 END) AS bar_metidos,
               sum(CASE WHEN cargando = 0 THEN p_ini - p_fin ELSE 0 END) AS bar_gastados,
               sum(CASE WHEN cargando = 1 THEN minutos ELSE 0 END)       AS min_cargando,
               sum(CASE WHEN cargando = 0 THEN minutos ELSE 0 END)       AS min_vacio
        FROM tramos WHERE roto = 0 AND lecturas > 1
    """).fetchone()
    metidos, gastados, t_carga, t_vacio = (float(v) for v in fila)
    # Cuánto tiempo se colaba por los huecos cuando la duración salía de restar
    # las marcas de tiempo. Va publicado porque es el tropiezo del módulo 26.
    roto = con.sql("""
        SELECT count(*), sum(span - minutos), sum(CASE WHEN roto = 1 THEN 1 ELSE 0 END)
        FROM tramos
    """).fetchone()
    return {
        "tramos": int(roto[0]),
        "tramos_con_hueco": int(roto[2]),
        "minutos_que_colaban_los_huecos": round(float(roto[1]), 0),
        "bar_metidos": round(metidos, 1),
        "bar_gastados": round(gastados, 1),
        "descuadre": round(abs(metidos - gastados) / gastados, 4),
        # Y en tanto por ciento, que es como se cita: el folio del módulo 31 y la
        # prosa del 24 escriben «0,7 %», no «0,0073».
        "descuadre_pct": round(abs(metidos - gastados) / gastados * 100, 1),
        "minutos_cargando": round(t_carga, 0),
        "minutos_en_vacio": round(t_vacio, 0),
        # La subida NETA por minuto de carga, ya descontado lo que se gasta
        # mientras tanto. No es la pendiente típica: es la media que mueve el aire.
        "sube_por_minuto_cargando": round(metidos / t_carga, 4),
        "consumo": round(gastados / t_vacio, 4),
        "carga_por_tramos": round(t_carga / (t_carga + t_vacio), 4),
    }


def pendientes_tipicas(con, desde: str, hasta: str) -> dict:
    """Las pendientes instantáneas, que es lo que se mide si nadie avisa.

    No son los parámetros del modelo. Están aquí porque **la diferencia con las
    medias es el hallazgo del módulo**: la mediana de llenado sale muy por encima
    de lo que el compresor consigue de verdad por minuto, porque cada carga
    empieza con el motor arrancando y termina con el depósito ya lleno
    empujando hacia atrás.
    """
    fila = con.sql(f"""
        WITH t AS (
          SELECT (lead(TP3) OVER (ORDER BY timestamp) - TP3) * 6 AS sube,
                 DV_eletric, lead(DV_eletric) OVER (ORDER BY timestamp) AS dv2,
                 date_diff('second', timestamp,
                           lead(timestamp) OVER (ORDER BY timestamp)) AS hueco
          FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        )
        SELECT median(CASE WHEN DV_eletric = 1 AND dv2 = 1 THEN sube END),
               median(CASE WHEN DV_eletric = 0 AND dv2 = 0 THEN -sube END)
        FROM t WHERE hueco = 10
    """).fetchone()
    # El escalón real del sensor, medido y no supuesto: el movimiento más pequeño
    # que TP3 llega a hacer. La primera versión daba por hecho que llevaba dos
    # decimales, o sea 0,01 bar en diez segundos y 0,06 bar/min, y publicaba que
    # la mediana instantánea de consumo caía justo ahí. Caía, pero de casualidad:
    # el escalón de verdad es diez veces más fino y no explica nada.
    escalon = float(con.sql(f"""
        SELECT min(s) FROM (
          SELECT abs(lead(TP3) OVER (ORDER BY timestamp) - TP3) AS s
          FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        ) WHERE s > 1e-9
    """).fetchone()[0])

    return {"llenado_mediana": round(float(fila[0]), 3),
            "consumo_mediana": round(float(fila[1]), 4),
            "escalon_del_sensor": round(escalon, 4),
            "escalon_en_bar_min": round(escalon * 6, 4),
            # Lo que la mediana instantánea se deja: el consumo no es parejo, va
            # a ráfagas, así que la mitad de los pasos quedan por debajo de la
            # media. Esto sí es la razón, y el escalón del sensor no lo era.
            "cuantos_escalones_es_la_mediana": round(float(fila[1]) / (escalon * 6), 1)}


def rampa(con, desde: str, hasta: str) -> list[dict]:
    """Lo que sube la presión en cada uno de los primeros pasos de una carga.

    Sobre la MISMA ventana sana que el resto de los parámetros. La primera
    versión la medía sobre el registro entero y salía descolgada de todo lo
    demás: una figura calibrada con otros datos que el modelo que ilustra.
    """
    filas = con.sql(f"""
        WITH c AS (
          SELECT tramo, TP3, row_number() OVER (PARTITION BY tramo ORDER BY timestamp) AS paso
          FROM (
            SELECT timestamp, TP3, DV_eletric,
                   sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
                       OVER (ORDER BY timestamp) AS tramo
            FROM (SELECT timestamp, TP3, DV_eletric,
                         lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
                  FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}')
          ) WHERE DV_eletric = 1
        ), d AS (
          SELECT paso, (TP3 - lag(TP3) OVER (PARTITION BY tramo ORDER BY paso)) * 6 AS sube
          FROM c
        )
        SELECT (paso - 1) * 10 AS segundo, count(*), median(sube)
        FROM d WHERE sube IS NOT NULL AND paso <= 11
        GROUP BY paso ORDER BY paso
    """).fetchall()
    return [{"segundo": int(s), "tramos": int(n), "bar_min": round(float(v), 3)}
            for s, n, v in filas]


def mide(desde: str = SANO[0], hasta: str = SANO[1]) -> tuple[Deposito, dict]:
    """Saca los cuatro números del lago. Ninguno se escribe a mano."""
    con = _lago()
    _crea_tramos(con, desde, hasta)
    arranca, para = conmutacion(con, desde, hasta)
    b = balance(con)
    tipicas = pendientes_tipicas(con, desde, hasta)
    la_rampa = rampa(con, desde, hasta)

    carga_real = float(con.sql(f"""
        SELECT avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END)
        FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
    """).fetchone()[0])

    # Cuántas veces arranca por hora. Es el segundo observable, y hace falta
    # porque el ciclo de trabajo **no puede ver** un error de tiempo: si las dos
    # duraciones se inflan por igual, su cociente no se mueve. Los arranques sí,
    # porque se cuentan contra el reloj. Ese es el hueco por el que se coló el
    # fallo de los huecos, y por eso este número está aquí ahora.
    arranques_real = float(con.sql(f"""
        WITH t AS (
          SELECT DV_eletric, lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
          FROM p WHERE day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        )
        SELECT sum(CASE WHEN antes = 0 AND DV_eletric = 1 THEN 1 ELSE 0 END)
                   / (count(*) * 10 / 3600.0)
        FROM t
    """).fetchone()[0])
    con.close()

    deposito = Deposito(arranca=round(arranca, 2), para=round(para, 2),
                        llena=b["sube_por_minuto_cargando"], consumo=b["consumo"])
    # Lo que el depósito tarda en subir y en bajar la banda entera, que es lo
    # que se puede contrastar contra el reloj sin creerse nada del modelo.
    periodo = deposito.banda / deposito.llena + deposito.banda / deposito.consumo
    contexto = {
        "ventana_sana": [desde, hasta],
        "carga_observada": round(carga_real, 4),
        "arranques_por_hora_observados": round(arranques_real, 3),
        "arranques_por_hora_que_predice": round(60 / periodo, 3),
        "minutos_por_ciclo": round(periodo, 2),
        "resolucion_del_sensor": tipicas["escalon_en_bar_min"],
        "ficha_arranque": FICHA_ARRANQUE,
        "ficha_alarma": FICHA_ALARMA,
        "balance": b,
        "pendientes_tipicas": tipicas,
        "rampa": la_rampa,
        # Lo que se lleva la mediana instantánea de lo que el compresor consigue
        # de verdad por minuto. Es el número que hizo fallar al primer gemelo.
        "cuanto_engana_la_mediana": round(
            tipicas["llenado_mediana"] / b["sube_por_minuto_cargando"] - 1, 3),
        # Y lo que ese engaño cuesta, que es lo que la lección publica: el ciclo
        # de trabajo que predeciría un modelo montado sobre la mediana. Se
        # calcula aquí para que el número esté medido y no recordado.
        "carga_con_la_mediana": round(
            b["consumo"] / (tipicas["llenado_mediana"] + b["consumo"]), 4),
        "error_con_la_mediana": round(
            abs(b["consumo"] / (tipicas["llenado_mediana"] + b["consumo"])
                - b["carga_por_tramos"]) / b["carga_por_tramos"], 3),
        # También en tanto por ciento, porque es como se cita en la prosa y
        # `check_numbers` compara la cifra escrita, no la fracción.
        "error_con_la_mediana_pct": round(
            abs(b["consumo"] / (tipicas["llenado_mediana"] + b["consumo"])
                - b["carga_por_tramos"]) / b["carga_por_tramos"] * 100, 1),
    }
    return deposito, contexto


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    deposito, contexto = mide()
    b, tipicas = contexto["balance"], contexto["pendientes_tipicas"]
    print(f"  la ventana sana va del {contexto['ventana_sana'][0]} "
          f"al {contexto['ventana_sana'][1]}")
    print()
    print(f"  arranca a          {deposito.arranca:>7.2f} bar   "
          f"(la ficha dice {contexto['ficha_arranque']})")
    print(f"  para a             {deposito.para:>7.2f} bar   (la ficha no lo dice)")
    print(f"  banda              {deposito.banda:>7.2f} bar")
    print()
    print("  el balance de aire, que es lo que decide si la medida vale:")
    print(f"    metidos          {b['bar_metidos']:>9.1f} bar")
    print(f"    gastados         {b['bar_gastados']:>9.1f} bar")
    print(f"    descuadre        {b['descuadre']:>9.1%}")
    print()
    print(f"  sube por minuto cargando  {deposito.llena:>7.4f} bar/min")
    print(f"  mediana instantánea       {tipicas['llenado_mediana']:>7.3f} bar/min   "
          f"un {contexto['cuanto_engana_la_mediana']:.0%} de más")
    print(f"  consumo                   {deposito.consumo:>7.4f} bar/min")
    print(f"  consumo, mediana instantánea {tipicas['consumo_mediana']:>5.4f} bar/min   "
          f"un {1 - tipicas['consumo_mediana'] / deposito.consumo:.0%} por debajo de la media")
    print(f"  escalón del sensor           {tipicas['escalon_del_sensor']:>7.4f} bar   "
          f"o sea {tipicas['escalon_en_bar_min']:.4f} bar/min, "
          f"{tipicas['cuantos_escalones_es_la_mediana']:.0f} veces menos que la mediana")
    print()
    print(f"  carga que predice el balance {deposito.consumo / deposito.entrega:>7.4f}")
    print(f"  carga observada              {b['carga_por_tramos']:>7.4f}")

    payload = {
        "arranca": deposito.arranca,
        "para": deposito.para,
        "banda": round(deposito.banda, 2),
        "llena": deposito.llena,
        "entrega": round(deposito.entrega, 4),
        "consumo": deposito.consumo,
        "carga_que_predice": round(deposito.consumo / deposito.entrega, 4),
        **contexto,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Tres cosas que tienen que cumplirse, o lo que se publica es falso.
    #
    #   1. El aire cuadra. Sin esto no hay medida que valga.
    if b["descuadre"] > 0.03:
        raise SystemExit(f"El aire no cuadra: {b['bar_metidos']} bar metidos contra "
                         f"{b['bar_gastados']} gastados, un {b['descuadre']:.1%}. "
                         "La medida está mal antes que el modelo.")
    #   2. Los dos parámetros predicen el ciclo observado. Es lo que convierte
    #      dos pendientes en un gemelo.
    predicha, observada = deposito.consumo / deposito.entrega, b["carga_por_tramos"]
    if abs(predicha - observada) / observada > 0.05:
        raise SystemExit(f"El modelo predice una carga de {predicha:.4f} y la máquina "
                         f"hizo {observada:.4f}. No se puede publicar como gemelo.")
    #   2b. Y los arranques por hora, que es la comprobación que faltaba. La de
    #      arriba comparte el error con lo que compara: si las dos duraciones se
    #      inflan por igual, su cociente no se mueve y el guardián no ve nada.
    #      Los arranques se cuentan contra el reloj, así que sí lo ven. Fue lo
    #      que destapó, en el módulo 26, que los huecos del registro se estaban
    #      contando como tiempo de compresor.
    pred_a = contexto["arranques_por_hora_que_predice"]
    obs_a = contexto["arranques_por_hora_observados"]
    if abs(pred_a - obs_a) / obs_a > 0.05:
        raise SystemExit(f"El modelo arranca {pred_a} veces por hora y la máquina "
                         f"{obs_a}. El ciclo de trabajo no puede ver esto: mira "
                         "las duraciones antes que el modelo.")
    #   3. La mediana instantánea se queda corta, y **no por culpa del sensor**.
    #      Las dos mitades van juntas a propósito: la primera es el hallazgo que
    #      publica el módulo 24, y la segunda es la explicación que se descartó.
    #      Si el escalón se acercara a la mediana, la culpa sí sería del sensor.
    corta = 1 - tipicas["consumo_mediana"] / deposito.consumo
    if corta < 0.2:
        raise SystemExit(
            f"La mediana instantánea de consumo ({tipicas['consumo_mediana']}) ya no "
            f"se queda corta frente a la media ({deposito.consumo}): solo un "
            f"{corta:.0%}. El módulo 24 publica que sí: hay que remirarlo.")
    if tipicas["cuantos_escalones_es_la_mediana"] < 3:
        raise SystemExit(
            f"La mediana instantánea vale {tipicas['cuantos_escalones_es_la_mediana']} "
            f"escalones de sensor. Tan cerca de la resolución, quien se queda corto "
            "es el instrumento y no la máquina: el módulo 24 dice lo contrario.")


if __name__ == "__main__":
    main()
