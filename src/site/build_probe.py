"""La página de pruebas del sistema visual. NO se publica.

Existe por una razón concreta: de los tres instrumentos del curso, el doble trazo
no aparece hasta el módulo 23, y descubrir allí que no funciona sería tarde. Aquí
se ve hoy, con datos de juguete declarados como tales.

Sigue el patrón de `prueba_scrolly.html` de Geoestadística, que tampoco se
publica: el build del portafolio la borra al espejar el curso.

Lo que enseña:
  - la carátula con la cifra, sobre el fondo real,
  - el doble trazo, con la regla de forma (medido continuo, simulado
    discontinuo) y el área entre curvas,
  - la perilla del caudal de fuga, que recalcula la simulación en vivo.

La física de juguete que hay detrás prefigura la del módulo 24, y usa los dos
umbrales reales de la máquina (arranca a 8,2 bar, alarma a 7).

Correr:  .venv\\Scripts\\python.exe src\\site\\build_probe.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_lesson import OUT_DIR, ROOT, TEMPLATES, build_rail, load_style, load_syllabus  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PAGE = """<!doctype html>
<html lang="es" class="no-js" data-assets="../assets">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Prueba del sistema visual · Fuelle</title>
<style>
{style}
:root {{ --accent: {accent_light}; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ --accent: {accent_dark}; }}
}}
:root[data-theme="dark"] {{ --accent: {accent_dark}; }}
</style>
</head>
<body>
<div class="shell">
  <aside class="panel">
    <span class="panel-brand">Fuelle<small>prueba del sistema visual</small></span>
    <nav class="rail"><p class="panel-label">el lago</p>{rail}</nav>
    <div class="panel-figure">
      <span class="v">8,2 bar</span>
      <span class="l">el umbral que arranca el compresor</span>
    </div>
    <div class="panel-progress">página de pruebas
      <span class="panel-bar"><i style="width: 100%"></i></span></div>
  </aside>

  <main class="stage">
    <div class="stage-inner">
      <header class="head">
        <p class="head-id"><b>prueba</b> <span>no se publica</span></p>
        <h1>Los tres instrumentos, juntos</h1>
        <p class="standfirst">Esta página no forma parte del curso. Existe para mirar los
        instrumentos antes de que las lecciones los necesiten, y sobre todo el doble trazo, que
        de otro modo no se vería hasta el módulo 23.</p>
      </header>

      <section class="block">
        <span class="kicker">Instrumento 1</span>
        <h2 class="block-title">La barra, con el lago en vertical</h2>
        <p>Está a la izquierda. Marca en qué capa trabaja la lección, deja la cifra a la vista
        mientras se lee, y no se mueve al bajar. Sustituye a la tira de treinta y un números, que
        ocupaba tres filas y no decía nada del recorrido.</p>
      </section>

      <section class="block">
        <span class="kicker">Instrumento 2</span>
        <h2 class="block-title">El doble trazo, y la perilla de la fuga</h2>
        <p><strong>Todo lo de este bloque es de juguete y se declara.</strong> Los datos no salen
        del compresor real: los calcula aquí mismo un modelo de tres líneas, con los dos umbrales
        que sí son reales, 8,2 bar para arrancar y 7 para la alarma.</p>

        <p>La curva continua es lo que mediría el sensor. La discontinua es lo que dice el gemelo
        que debería pasar. <strong>El color nunca es la única pista</strong>: si se imprime en
        blanco y negro, o si quien mira no distingue el tono, el trazo las sigue separando.</p>

        <p><strong>Son dos gráficos porque hacen falta dos.</strong> Al construir esta página, el
        primer intento dibujaba solo la presión, y al mover la perilla las dos curvas no se
        separaban: 32 px de distancia media con 5 l/min de fuga y 31 px con 40. Medido, no
        supuesto. La razón es la tesis del curso, cometida contra el propio instrumento: la
        presión es la variable <em>controlada</em>, y el control la sostiene entre 8,2 y 9,5 pase
        lo que pase. El primer gráfico enseña justo eso, que ahí no se ve nada.</p>

        <div class="knob">
          <label for="fuga">caudal de fuga</label>
          <input type="range" id="fuga" min="0" max="40" value="0" step="1">
          <output id="fugaval">0 l/min</output>
        </div>

        <p class="live-status">1. La presión del depósito. Aquí la fuga no se ve.</p>
        <div class="twin" id="twin"></div>

        <p class="live-status">2. El trabajo acumulado. Aquí sí.</p>
        <div class="twin" id="twin2"></div>

        <p class="twin-key">
          <span class="k-measured"><i></i>medido, el sensor</span>
          <span class="k-simulated"><i></i>simulado, el gemelo</span>
        </p>
        <p id="verdicto" class="live-status"></p>
      </section>

      <section class="block">
        <span class="kicker">Instrumento 3</span>
        <h2 class="block-title">La carátula</h2>
        <p>Es la caja de la barra con la cifra del módulo. No lleva aguja animada: se probó la
        idea y no pasaba el filtro de si al quitarla se entiende peor. La cifra sola dice más.</p>
      </section>

      <footer class="footer">
        <span>Fuelle / prueba del sistema visual</span>
        <span>no se publica</span>
      </footer>
    </div>
  </main>
</div>

<script>
/* El compresor de juguete. Un deposito que se llena cuando el compresor carga y
   se vacia con el consumo, mas la fuga. El gemelo simula SIN fuga.

   Se devuelven DOS series por corrida, y ese es el hallazgo que esta pagina
   destapo: la presion no sirve para ver la fuga, porque es la variable que el
   control sostiene. Medido al construir esto: 32 px de separacion media con
   5 l/min de fuga y 31 px con 40. El trabajo acumulado si diverge, porque es la
   variable manipulada. Es la tesis del curso, cometida contra el instrumento. */
const MIN = 8.2, MAX = 9.5, PASOS = 220;

function simular(fugaLpm) {{
  const consumo = 22, caudal = 95, k = 0.011;   // l/min, l/min, bar por litro
  let p = 9.5, cargando = false, acumulado = 0;
  const presion = [], trabajo = [];
  for (let t = 0; t < PASOS; t++) {{
    if (p <= MIN) cargando = true;
    if (p >= MAX) cargando = false;
    const entra = cargando ? caudal : 0;
    p += k * (entra - consumo - fugaLpm) / 6;
    if (cargando) acumulado += 1;
    presion.push(p);
    trabajo.push(acumulado);
  }}
  return {{presion, trabajo}};
}}

function trazo(serie, m, w, h, lo, hi) {{
  return serie.map((v, i) => {{
    const x = m.l + (i / (serie.length - 1)) * w;
    const y = m.t + h - ((v - lo) / (hi - lo)) * h;
    return `${{i ? "L" : "M"}} ${{x.toFixed(1)}} ${{y.toFixed(1)}}`;
  }}).join(" ");
}}

function grafico(destino, real, gemelo, lo, hi, marcas, etiqueta) {{
  const W = 900, H = 190, m = {{l: 46, r: 14, t: 12, b: 22}};
  const w = W - m.l - m.r, h = H - m.t - m.b;

  const area = trazo(real, m, w, h, lo, hi) + " " +
    gemelo.map((v, i) => {{
      const j = gemelo.length - 1 - i;
      const x = m.l + (j / (gemelo.length - 1)) * w;
      const y = m.t + h - ((gemelo[j] - lo) / (hi - lo)) * h;
      return `L ${{x.toFixed(1)}} ${{y.toFixed(1)}}`;
    }}).join(" ") + " Z";

  const ticks = marcas.map(v => {{
    const y = m.t + h - ((v - lo) / (hi - lo)) * h;
    return `<path class="axis" d="M ${{m.l}} ${{y}} H ${{W - m.r}}" opacity=".4"/>` +
           `<text class="tick" x="${{m.l - 8}}" y="${{y + 3}}" text-anchor="end">${{v}}</text>`;
  }}).join("");

  document.getElementById(destino).innerHTML =
    `<svg viewBox="0 0 ${{W}} ${{H}}" role="img" aria-label="${{etiqueta}}">
       ${{ticks}}
       <path class="gap" d="${{area}}"/>
       <path class="simulated" d="${{trazo(gemelo, m, w, h, lo, hi)}}"/>
       <path class="measured" d="${{trazo(real, m, w, h, lo, hi)}}"/>
     </svg>`;
}}

function arranques(serie) {{
  return serie.reduce((n, v, i) => n + (i && serie[i-1] > MIN && v <= MIN ? 1 : 0), 0);
}}

function pintar(fuga) {{
  const real = simular(fuga);
  const gemelo = simular(0);

  grafico("twin", real.presion, gemelo.presion, 6.8, 9.8, [7, 8, 8.2, 9, 9.5],
          "presion del deposito, medida contra simulada");

  const tope = Math.max(...real.trabajo, ...gemelo.trabajo);
  const paso = Math.ceil(tope / 4 / 10) * 10;
  const marcas = [0, paso, paso * 2, paso * 3, paso * 4].filter(v => v <= tope * 1.05);
  grafico("twin2", real.trabajo, gemelo.trabajo, 0, tope * 1.05, marcas,
          "trabajo acumulado, medido contra simulado");

  const extra = real.trabajo[PASOS - 1] - gemelo.trabajo[PASOS - 1];
  const pct = gemelo.trabajo[PASOS - 1]
    ? Math.round(100 * extra / gemelo.trabajo[PASOS - 1]) : 0;

  document.getElementById("verdicto").textContent = fuga === 0
    ? "Sin fuga las dos curvas se pisan en los dos graficos, y el area entre ellas es nula."
    : `Con ${{fuga}} l/min: la presion sigue entre 8,2 y 9,5 y el primer grafico no delata nada. `
      + `El compresor arranca ${{arranques(real.presion)}} veces frente a `
      + `${{arranques(gemelo.presion)}}, y trabaja un ${{pct}} % mas. Esa es la senal.`;
}}

const perilla = document.getElementById("fuga");
perilla.addEventListener("input", () => {{
  document.getElementById("fugaval").textContent = perilla.value + " l/min";
  pintar(+perilla.value);
}});
document.documentElement.classList.remove("no-js");
pintar(0);
</script>
</body>
</html>
"""


def main() -> None:
    syllabus = load_syllabus()
    accent = syllabus["modules"][22]["accent"]  # el del módulo 23, el del gemelo
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / "prueba_visual.html"
    target.write_text(
        PAGE.format(
            style=load_style(),
            rail=build_rail(23, "es"),
            accent_light=accent["light"],
            accent_dark=accent["dark"],
        ),
        encoding="utf-8",
    )
    print(f"  {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")
    print("  NO se publica: el espejado del portafolio la deja fuera")


if __name__ == "__main__":
    main()
