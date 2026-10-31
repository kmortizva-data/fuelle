# Auditoría visual del curso Fuelle (2026-10-30)

Misma pregunta que se le hizo a Sílice el día antes: ¿qué está ya a nivel en lo visual y qué no?
Respuesta con evidencia, módulo a módulo, sobre las páginas construidas en `out/` (español,
comprobando que el inglés lleva lo mismo), el índice, el panel y el folio. Solo lectura: no se
cambió ninguna figura, página ni script.

**Cómo se miró.** Seis lectores en paralelo, uno por tramo del curso, leyeron cada lección
entera y abrieron **cada una de las 39 figuras en tres variantes** (oscuro y claro en español,
oscuro en inglés: 117 PNG), con recortes ampliados al doble donde había duda de un pisado. Las
páginas se miraron en el navegador a 1440 px y a 375 px, en oscuro y en claro. Los hallazgos que
afirman que algo publicado es falso se comprobaron otra vez contra el JSON o el HTML antes de
escribirlos aquí.

## Veredicto en una frase

La piel ya está a nivel y es la mejor del portafolio (las 39 figuras con la paleta del curso,
en dos temas y dos idiomas, con huellas al día y una guarda que impide cadenas sin traducir);
lo que falla es lo mismo que en Sílice salvo la piel: **ningún ejemplo de juguete tiene dibujo
(0 de 31)**, la primera figura llega **a mitad de la lección** (mediana 48 %), dos lecciones
clave no tienen ninguna figura, y hay **siete textos o figuras publicados que dicen algo falso**
que ninguna de las diez puertas ve.

## Cifras del curso

| Qué | Medido |
|---|---|
| Palabras (español / inglés) | 56.908 / 56.927 |
| Figuras únicas | 39, en 156 PNG (2 temas x 2 idiomas) |
| Figuras con la paleta del curso | 39 de 39 (cero colores fijos en los 29 scripts) |
| Figuras con alguna cadena sin traducir en inglés | 0 |
| PNG huérfanos / huellas `?v=` viejas en las páginas | 0 / 0 |
| Figuras en «El resultado, medido» | 36 de 39 |
| «Antes de la teoría: un ejemplo de juguete» con dibujo | **0 de 31** (son 33 tablas y prosa) |
| Primera figura de cada lección | del 30 al 55 % del texto, mediana 48 % (el 31, al 14 %) |
| Lecciones sin ninguna figura | 2: el 10 (la lección de muestra) y el 11 |
| Perillas (doble trazo) | 5, módulos 24 a 28 |
| Diagramas de cajas en HTML | 4, módulos 4, 8, 11 y 15 |
| Bloques de código | 107, de ellos 16 consultas vivas, más 15 retos |
| Tablas | 51 (33 en los juguetes, 18 en los resultados) |
| Figuras con `figcaption` | 0 (el `alt` es el nombre del fichero) |
| Tipografía real de las figuras | Consolas, no la Plex Mono de la página |
| Índice / folio | 0 figuras / 0 figuras y 1 tabla |
| Panel | 2 SVG en línea, estado completo sin JavaScript |

## Módulo a módulo

Estilo: las 39 figuras usan la paleta del curso, así que la columna dice qué más se vio. La
primera figura es el porcentaje de prosa que se lee antes de llegar a ella; entre paréntesis, el
primer elemento visual cuando es un diagrama o una perilla.

| Módulo | Palabras | Figuras | Estado visual | 1.ª figura | Lo de más rendimiento |
|---|---|---|---|---|---|
| m01 El encargo | 1.650 | 2 | umbral y «#1» pisados; la prosa dice martes y el día dibujado fue lunes | 30 % | esquema de la máquina con cada una de las 15 señales en su pieza; tira de 3.600 pesadas contra 360 |
| m02 Dato, tabla, tipo | 1.562 | 1 | «nada en medio» atravesado por el escalón de COMP | 43 % | la rejilla del cuaderno con fila, columna y grano; raya a las 08:19 que cruce los dos paneles |
| m03 Dónde viven los datos | 1.820 | 1 | el bigote tacha «0,003» y «0,004» | 42 % | los cuatro sitios del juguete como iconos; «186 veces» y «no se distinguen» dentro de la figura |
| m04 Bronce | 1.665 | 1 + diagrama | sin pisados; ticks sin punto de millar | 52 % (44 %) | las seis lecturas con el -10,0 y las dos medias; raya del 90 % en la figura |
| m05 Idempotencia | 1.672 | 1 | ninguno; la figura más limpia de la parte 2 | 49 % | rejilla de 256 bits con los 126 que cambian, del XOR real |
| m06 Particionar | 1.425 | 1 | «16,84» fuera del área; ticks con punto | 44 % | carpetas que se abren (1, 1, 30); bloques con su mínimo y máximo saltados |
| m07 Filas contra columnas | 1.897 | 2 | **el resumen dice 25 y es 22**; «181 veces» destacado aunque es inestable | 44 % | rejillas por filas y por columnas (12 celdas contra 4); escalera de 16,84 a 0,03 MB |
| m08 Primera consulta | 1.759 | 1 + diagrama | **pie invertido en tema claro**; sin escala de color | 48 % (37 %) | la tabla del juguete tres veces (SELECT, WHERE, ORDER BY con LIMIT); orden de ejecución numerado en el diagrama |
| m09 Tipos y decisiones | 1.786 | 2 | doble espacio; pico de 8,26 sin explicar | 46 % | perilla de los cortes de 1 y 5 A; curva de filas contra margen (107, 498, 5.237) |
| m10 Agrupar | 2.009 | **0** | ninguna figura; el editor esconde ORDER BY y LIMIT | sin figura | ciclo de trabajo de los 212 días con los seis del top; antes y después del filtro de días completos |
| m11 Consultas por pasos | 1.401 | **0** + diagrama | el editor enseña 4 de 15 líneas | (47 %) | barras de rango solapadas, reutilizables en el 6, el 19 y el 26 |
| m12 Juntar tablas | 1.609 | 2 | etiqueta de la raya confundida con la del INNER; dobles espacios; #3 y #4 casi invisibles | 49 % | el juguete T1 con dos incidencias (300 t que se vuelven 400); línea de tiempo de los cuatro partes |
| m13 Ventanas | 1.662 | 1 | la anotación la cruzan las líneas de arranque | 48 % | histograma de los huecos del lago con el de 48 h; arranques contra horas de carga por día |
| m14 Plata | 1.840 | 2 | la leyenda tapa la barra de agosto y su «18 %» | 45 % | el reloj que camina: rejilla fija contra lecturas que se deslizan |
| m15 Otras fuentes | 1.704 | 1 + diagrama | ninguno; la figura más didáctica de la parte 4 | 49 % (43 %) | pesadas y leyes del juguete; raya a las 10:00 y «75,7 °C» en la figura |
| m16 Calidad | 1.652 | 1 | rótulos sin tildes en español; salidas en español en la edición inglesa | 45 % | lotes dentro y fuera de la banda; matriz antes y después de la octava promesa |
| m17 Oro con dbt | 2.142 | 1 | flechas en el color de la rejilla, casi invisibles en claro | 51 % | pizarra contra código (3 cajas contra 4); «9 nodos, 8 dependencias» en la figura |
| m18 Viaje en el tiempo | 1.919 | 2 | meses en inglés en la española; coma y punto en la misma figura | 50 % | el cuaderno junto a los ficheros; panel de disco (12,9 contra 53,7 KB) |
| m19 PostgreSQL | 1.915 | 1 | ticks con punto | 52 % | mostrador contra cuaderno; topología cliente y servidor como diagrama |
| m20 Esquema | 1.715 | 1 | la rejilla enciende 21 celdas y la prosa habla de 12 guardas | 48 % | marcar las seis guardas que rechazaron; la libreta con cuatro imposibles |
| m21 Índices | 1.615 | 1 | **figura española caducada**; ticks con punto | 49 % | archivador contra fichero ordenado; los dos planes como árboles |
| m22 Mantenimiento | 1.510 | 1 | sin título en los paneles | 49 % | las 24 copias con 14 vacías; flujo copiar, restaurar, comparar |
| m23 Qué es un gemelo | 1.752 | 1 | ninguno | 40 % | los dos hornos que se separan; «1.335,7 min» dentro de la figura |
| m24 Física | 1.938 | 1 + perilla | «6 % de más» pisado; perilla sin escala | 48 % (45 %) | el diente de sierra del tanque del juguete; barras del balance |
| m25 Simular | 1.798 | 2 + perilla | anotación sobre línea y barra; **la perilla dice 7 arranques en todas las posiciones** | 41 % (39 %) | depósito con tres rejillas de muestreo; perilla simulada a 8 h |
| m26 Calibrar | 2.425 | 3 + perilla | superficie de error sin barra de color | 38 % (35 %) | tiras de pulsos de los dos técnicos; la LPS como quinto panel |
| m27 Residual | 2.242 | 1 + perilla | anotación tachada; leyenda cruzada; «-0,0×» en la perilla | 38 % (32 %) | dos acumulados que se separan 1.200 l; días sobre el suelo, mes a mes |
| m28 Veredicto | 2.460 | 2 + perilla | **la nota de la perilla es falsa**; sin leyenda para raya y banda | 30 % (28 %) | la matriz 2, 0, 48, 313; barras gemelo contra LPS |
| m29 Orquestar | 2.654 | 1 | «214 días» tachado por flechas; notas a 7 px | 52 % | el grafo de cuatro tareas del juguete; el experimento de hilos en barras |
| m30 Panel | 2.184 | 1 + panel | raya punteada sin etiqueta | 55 % | las dos escaleras del redondeo; los 214 días por clase en una barra |
| m31 Entregar | 1.526 | 1 | arco de 5,78 a 1, ilegible en móvil | 14 % | el arco como bloque `diagrama`, que ya existe |
| Índice | 1.739 | 0 | limpio en los dos temas y a 375 px; la paleta solo sale al pasar el ratón | sin figura | la tira del semestre ya precalculada; una cifra de cabecera del curso; la paleta visible |
| Panel | 663 | 2 SVG | leyenda sin las rayas verticales ni lo de la tira | arriba | barras de la tira con el color de su clase |
| Folio | 613 | 0 + 1 tabla | una cara, papel forzado, correcto | sin figura | una barra junto a la tabla: 1,5 contra 11,4 falsas al mes |

La edición inglesa lleva las mismas figuras y los mismos bloques en las 31 lecciones (comprobado
por recuento de `{{FIG:}}` y de cercas), con dos salvedades: los dos bloques `salida` del 16 en
español, que es una limitación declarada pero la lección no la avisa, y la leyenda del 27, que al
alargarse en inglés toca la nota del techo.

## Defectos de maqueta concretos

### Lo publicado que dice algo falso (va primero)

1. **m21 `fig_m21_indice_antes_despues`, las dos españolas están caducadas.** Enseñan 0,2943 /
   0,0038 / 0,524 / 1,240 s; `results/m21_indices.json`, la tabla de la misma lección y los PNG
   ingleses dicen 0,2925 / 0,0027 / 0,494 / 1,208. Los españoles son del 2026-09-02 y los
   ingleses del 09-03: se rehízo solo el inglés. Ninguna puerta compara un PNG con su JSON.
2. **m08 `fig_m08_null_no_es_cero`, tema claro.** El pie dibujado dice «cuanto más clara más
   saltó la alarma» y en claro es al revés: las casillas con más alarma son las más oscuras. El
   texto es fijo en el script y no cambia con el tema. Igual en inglés.
3. **m07, «En 30 segundos».** Dice «de 54 veces a **25**» en los dos idiomas; el cuerpo, el
   repaso, la figura y `results/m07_formats.json` dicen 22. Residuo de la corrección del
   2026-09-19 que `check_numbers` no cazó porque hay un 25 en otro fichero de resultados.
4. **m28, perilla del umbral.** La nota fija dice «la línea de puntos es la referencia, con 1,15
   bar/min» y esa línea son los 7 días con avería real; la lección lo explica bien un párrafo
   antes. Es la nota genérica del renderizador aplicada donde no vale.
5. **m25, perilla del paso.** `arranques` vale 7 en las diez posiciones del JSON (de 0,1 a 120 s),
   porque en 4 horas simuladas no se pierde ningún ciclo, y la prosa promete escalones «más largos
   y más pocos». La tabla de la lección que sí pierde ciclos es la de 8 horas.
6. **m01, «dos horas de un martes cualquiera».** La figura dibuja el 2020-02-10, que fue lunes.
   Igual en inglés.
7. **m20 `fig_m20_esquema`.** La rejilla enciende 21 celdas y la prosa dice «en la figura se ve el
   reparto» de 12 guardas: «no vacío» no es una restricción y un CHECK cubre dos columnas. Falta
   un total por columna y una línea que lo explique.

### En las figuras

8. **Ticks que no pasan por `es()`**: en la edición española conviven «8,2» en la anotación y
   «8.5» en el eje en m01, m02, m06, m18 (Delta contra Iceberg), m19 y m21; m04 escribe «8000»
   junto a «8.640», y m14 «300000» sin punto de millar. Un solo arreglo en `figures_theme`.
9. m01 `fig_m01_anatomia_del_compresor`: «8,2 bar: el umbral de arranque» atravesada por la curva
   y la banda; el eje dice «10 08:00» con el día del mes delante sin explicar.
10. m01 `fig_m01_las_cuatro_averias`: «#1» bajo la leyenda y pisado por el anillo; «media 3.42 h»
    con punto en español.
11. m02 `fig_m02_analogica_vs_digital`: «nada en medio» cruzado por el escalón de las 08:19.
12. m03 `fig_m03_cuatro_sitios`: el bigote del rango tacha el primer dígito de «0,003» y «0,004».
13. m06 `fig_m06_curva_de_particion`: «16,84» se sale del área y en inglés toca el título del eje.
14. m07 `fig_m07_csv_vs_parquet`: «181 veces» pegado a la leyenda, y es la cifra que la prosa
    retira por inestable sin que la figura lo marque.
15. m08: la etiqueta «2020-04-26» pisa dos casillas; las filas del calendario no dicen que son
    días de la semana; no hay escala de color.
16. m09 `fig_m09_coma_flotante`: doble espacio en «encuentra  TP2»; el pico del cajón de 8,26 sin
    explicar.
17. m12 `fig_m12_tipos_de_join`: la etiqueta de la raya de 1.516.948 se lee como parte de la
    anotación del INNER; 40 % del eje vacío; dobles espacios por un `replace` con dos espacios. En
    `fig_m12_join_que_multiplica`, las líneas de #3 y #4 en color de rejilla casi no se ven.
18. m13 `fig_m13_lag_y_hueco`: las tres primeras líneas de arranque cruzan la anotación; la raya
    de referencia de 10 s queda enterrada bajo los puntos.
19. m14 `fig_m14_huecos`: la leyenda (`loc="upper right"`) tapa la barra de agosto y su «18 %».
20. m16 `fig_m16_contrato_roto`: rótulos sin tildes en español («presion», «dia», «mas»), que
    vienen de los nombres ASCII de `contracts.py`.
21. m17 `fig_m17_linaje_dbt`: flechas en `c["rule"]`, el color pensado para desaparecer; en claro
    los cruces diagonales apenas se siguen, y son lo único que la figura tiene que enseñar.
22. m18 `fig_m18_historial_de_versiones`: meses en inglés en la española («Apr», «Aug») por
    `DateFormatter("%b")`; las cuatro rayas de las averías, casi invisibles en claro.
23. m22 `fig_m22_copia_y_restauracion`: la única de su parte sin título en los paneles.
24. m24 `fig_m24_balance_del_deposito`: «6 % de más» escrita sobre la mediana y sobre un punto.
25. m25 `fig_m25_paso_de_tiempo`: la anotación de dos líneas cruza la línea punteada y la barra de
    20 s, peor en inglés; marcas de 0,5 en un eje de ciclos enteros.
26. m26 `fig_m26_ajuste`: tres superficies de error sin barra de color ni «más oscuro, menos
    error»; los 40 puntos empatados del panel central se funden con la banda.
27. m27 `fig_m27_residual`: «el suelo de febrero» tachada por los picos de marzo; la leyenda sin
    fondo la cruzan las rayas de junio; en inglés la leyenda toca la nota del techo; el panel de
    abajo sin unidad.
28. m28 `fig_m28_cuatro_averias`: sin leyenda para la raya de 1,15 ni para la banda del parte.
29. m29 `fig_m29_grafo_de_activos`: «214 días» cruzado por dos flechas; el borde naranja del
    gemelo no está en el pie; las notas al pie llegan a unos 7 px.
30. m30 `fig_m30_peso_del_semestre`: la raya punteada horizontal, que es el hallazgo «raro» de
    la prosa, no lleva etiqueta.
31. m31 `fig_m31_arco_del_proyecto`: 1.423 por 246 px; a 980 px los rótulos quedan en unos 7 px y
    a 375 px no se lee nada.

### En la página

32. **El editor de la consulta viva enseña unas cinco líneas** (`min-height: 112px`, sin `rows` ni
    ajuste en `live.js`). En el 10 esconde ORDER BY y LIMIT; en el 11 enseña 4 de 15 líneas, en el
    módulo cuyo mensaje es «ahora se lee de arriba abajo». También el 9, el 12, el 13 y el 17.
33. **Las perillas no tienen escala.** El SVG trae dos caminos y nada más: ni minutos, ni las 4 u 8
    horas simuladas, ni el techo. Y en la posición de partida el trazo coincide con la referencia
    (idéntico en el 25 y el 27, superpuesto a la vista en el 24 y el 26), así que **sin
    JavaScript se ve una sola línea**. El 27 escribe «-0,0× el suelo» en la posición cero.
34. **Ninguna figura lleva pie.** El `<figure class="fig">` tiene dos `<img>` y nada más; el `alt`
    es el nombre del fichero («fig m23 gemelo y residual»). El CSS de `figcaption` existe y no lo
    usa nadie.
35. **El panel**: la leyenda no explica las tres rayas verticales (alarma, parte, cierre) ni, en la
    tira, el suelo punteado y el subrayado naranja de marzo; las barras altas de la tira no
    distinguen acierto de falsa alarma aunque `pg-clase` ya tiene esos colores.
36. **El índice**: cada fila del temario lleva su acento, pero solo se ve al pasar el ratón, así
    que los 31 colores calculados no se ven nunca juntos; «31 / 31 lecciones escritas» es una
    cifra de obra que ya no informa.
37. m16 inglés: dos bloques `salida` en español sin una línea que lo avise.

## Cómo se construyen las figuras y las perillas hoy

**Lo que ya está a nivel, con evidencia.**

- **Una sola paleta, sin colores a mano.** Los 29 scripts `src/figures_moduleN.py` pasan por
  `src/figures_theme.py`, que lee `results/palette.json` (31 acentos en OKLCH medidos en contraste
  sobre los dos fondos) y los tokens de los dos temas, los mismos de `_base.css`. Un `grep` de
  `tab:`, hexadecimales o mapas de color en los 29 scripts devuelve cero. En Sílice eran 16 de 56.
- **Dos temas de nacimiento.** Cada figura sale en claro y en oscuro y la página conmuta con dos
  `<img>`. Comprobado en el navegador: al pasar a claro, la figura del 24 y la perilla cambian de
  piel con la página.
- **Inglés sin tocar los scripts y con guarda.** `figures_i18n.py` parchea `Text.set_text`,
  `Artist.set_label` y `Figure.savefig`; `figures_build_en.py` corre cada script en su proceso y
  **falla si queda una cadena visible sin traducir**. Los seis lectores no encontraron ninguna.
- **Huellas al día y nada huérfano.** Las 156 referencias `?v=` de las páginas coinciden con el
  SHA256 de su PNG, y las 39 figuras referenciadas son exactamente las 39 del disco.
- **Las perillas, honestas por construcción.** `src/twin/simulate.py` simula una vez en Python por
  posición; `render_lesson.perilla_block` dibuja en el servidor los dos caminos y el pie;
  `perilla.js` solo cambia de serie. `check_motion.py` vigila el estado sin JavaScript,
  `prefers-reduced-motion`, un instrumento por lección, la interacción prometida y la huella de los
  datos. La regla de forma (medido continuo, simulado discontinuo) se cumple en las figuras del
  gemelo y en el panel.
- **El panel es la mejor pieza del portafolio.** Estado completo sin JavaScript, textos en HTML
  que sobreviven a 375 px, tres modos de elegir día, `aria-live` en la frase y la huella en la URL.
- **Los diagramas en HTML** (bloque `diagrama`) resuelven tema y móvil con CSS y se apilan con la
  flecha girada a menos de 640 px. Es el patrón que le falta al arco del 31.

**Lo que no está a nivel, con evidencia.**

- **La tipografía.** `_style` pide IBM Plex Mono, pero matplotlib no la encuentra y resuelve a
  `C:\Windows\Fonts\consola.ttf`: las 156 figuras están en Consolas. La página sirve Plex en
  `woff2`, que matplotlib no lee; hace falta el `.ttf` registrado en `figures_theme`.
- **El tamaño de letra que llega a la pantalla.** Los PNG miden de 1.167 a 1.423 px a 150 dpi y se
  enseñan a 980 como mucho, o sea al 69 a 84 %. Un rótulo de 8 pt llega a unos 11,7 px; los de 6 a
  7 pt del 29 y el 31 a unos 8,8 px, por debajo del pie de figura de la propia página (12,5 px).
- **Los ticks.** El separador decimal de las etiquetas lo pone `es()`, pero el de los ejes lo pone
  matplotlib, y nadie lo cambia (defecto 8).
- **Ninguna puerta mira el PNG contra su JSON.** `check_lesson` comprueba que existan los cuatro
  ficheros; `check_numbers` compara la prosa con `results/`. Así sobrevivió la figura caducada del
  21 desde el 2 de septiembre.
- **El campo `instrumento` no cambia la página.** El temario reparte 13 «grafo», 11 «carátula» y 7
  «doble trazo», pero las 31 páginas llevan siempre el mismo riel de cinco etapas y la misma
  cifra en la barra; el campo solo lo lee `check_motion` para contar perillas. El «grafo de
  nodos» que iba a enseñar qué construye cada lección no existe como pieza propia: su versión real
  es el riel y los cuatro diagramas. Es también lo que bloquea tres perillas útiles (9, 6 y 21),
  porque esos módulos declaran otro instrumento.

## Propuesta, en orden de rendimiento por esfuerzo

1. **Que nada publicado diga algo falso** (horas). Regenerar las dos españolas del 21; el pie del
   8 según el tema; el 25 por el 22 en el resumen del 7; el lunes del 1; la nota de la perilla del
   28 desde el JSON, como ya hace la del 27; el cero negativo del 27; la perilla del 25 simulada a 8
   horas o la prosa ajustada a lo que enseña; el total por columna en la rejilla del 20. Y una
   guarda nueva en `check_lesson`: **ningún PNG puede ser más viejo que el JSON del que sale**.
2. **La piel común, sin tocar los 29 scripts** (un día). Plex Mono registrada en `figures_theme`;
   un formateador de ejes que pase por `es()`, inyectado igual que el parche de idioma; un pie y un
   `alt` por figura leídos de `temario.json`; el editor de la consulta viva con tantas filas como
   líneas tenga el SQL; tamaño mínimo de rótulo de 8 pt. Mismos números: las puertas lo prueban.
3. **Los defectos de colocación**, script a script (del 9 al 31 de la lista, unos veinte). Patrón
   ya resuelto en el propio curso: la caja de fondo del 4 y la leyenda que concluye del 5. El arco
   del 31 pasa a bloque `diagrama`.
4. **Las perillas legibles** (un día). Escala mínima en el SVG (techo en minutos, duración
   simulada, el suelo en el 27), posición de partida separada de la referencia o referencia igual
   a la máquina medida, y la leyenda del panel con las rayas y la tira con el color de su clase.
5. **Un dibujo por ejemplo de juguete** (31), SVG generado en el build con los números del propio
   juguete y afirmados contra él, como hizo Sílice en su fase 3. Primero los que ya tienen forma
   de dibujo: 7 (filas contra columnas), 4 (el -10,0), 12 (T1 con dos incidencias), 8 (SELECT y
   WHERE sobre seis filas), 17 (pizarra contra código), 29 (grafo de cuatro tareas), 23 (dos
   hornos), 24 (diente de sierra), 28 (matriz 2, 0, 48, 313), 14 (el reloj que camina).
6. **La cifra del módulo dentro de su figura, y las figuras que faltan.** La del 10 (el ciclo de
   trabajo de los 212 días, que el temario prometió como `fig_m10_ciclo_de_trabajo_diario` y se
   retiró sin dibujar) y una para el 11; anotaciones de la cifra en 14, 15, 17, 18, 20, 21, 22 y
   23; el índice con la tira del semestre (ya precalculada, 26,5 KB), una cifra de cabecera del
   curso y la paleta visible en reposo; una barra junto a la tabla del folio.
7. **Perillas nuevas donde el concepto es un parámetro**, con datos medidos: los cortes de 1 y 5 A
   del 9, el número de ficheros del 6 y la selectividad del índice del 21 (este exige medirla).
   Obliga a decidir antes qué significa `instrumento`: o se reparte de verdad en la página, o se
   deja de exigir uno por lección.

**Lo que no cambia:** ninguna cifra publicada salvo las siete que hoy están mal (fase 1). Cada
fase pasa por las diez puertas y por Kevin, que mira cada figura antes de publicar. Las fases 1 a
3 dejan el curso sin defectos visibles; las 4 a 7 son las que lo separan de un PDF, que es el
encargo original.
