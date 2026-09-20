# El veredicto, en un folio

## La pregunta

¿Un modelo de la física de un compresor, calibrado con un mes sano y sin ver ninguna avería,
avisa de las fugas de aire mejor que la alarma que la máquina ya lleva?

## El método, en cinco líneas

1. **{lecturas} lecturas** de {senales} señales, una cada diez segundos, siete meses del compresor
   de aire de un tren del Metro de Oporto: {mb_csv} MB de CSV, de la UCI, con licencia CC BY 4.0.
2. Un **lago de datos por capas**, con las lecturas en una rejilla regular de diez segundos, y las
   mismas servidas desde PostgreSQL.
3. **Cuatro números medidos de febrero** describen la máquina: arranca a {arranca} bar, para a
   {para}, llena a {llena} bar por minuto y la planta gasta {consumo}. El aire que entra y el que
   sale cuadran al {descuadre} %.
4. El **gemelo** corre en paralelo con esos cuatro números congelados. Lo único que se mira es su
   discrepancia con la máquina, el **residual**, en bar por minuto.
5. El umbral no se elige: se **barre entero**. El más alto que todavía pilla las cuatro averías
   documentadas es {umbral} bar por minuto.

## El veredicto

| Sobre los {dias_juzgados} días que el gemelo puede juzgar | El gemelo | La alarma instalada |
|---|---|---|
| Averías detectadas | **{detectados} de {sucesos}** | {lps_detectados} de {sucesos} |
| Días con alarma | {dias_alarma} | {lps_dias} |
| Falsas alarmas al mes | **{falsas_mes}** | {lps_falsas_mes} |

**Lo que no hace: predecir.** Solo una de las cuatro avisa antes, y con un día. Una fuga de aire
no crece despacio: se abre, y el compresor pasa de trabajar una vigésima parte del tiempo a no
parar en unas horas.

**Lo que encontró sin que nadie lo pidiera.** Doce días de marzo con la máquina averiada y sin
parte de mantenimiento, y cuatro señales independientes lo dicen a la vez. Contando marzo como
avería, el resultado es {marzo_detectados} de {marzo_sucesos} con {marzo_falsas} falsas al mes.

## Qué se rompería en una planta de verdad

- **Una sola máquina.** Los cuatro números son de este compresor; otro exige medirlos de nuevo, y
  basta un mes sano.
- **Cuatro averías no son una muestra.** Es un estudio de cuatro casos, y un acierto de más o de
  menos mueve el resultado.
- **Sin el volumen del depósito no hay litros.** El residual va en bar por minuto, y pasarlo a
  caudal exige un dato que la ficha no da.
- **Ninguna fuga de referencia.** Nadie abrió una válvula de tamaño conocido, así que la escala de
  gravedad no está calibrada.
- **La máquina se degrada.** El consumo sano dobla entre febrero y agosto, y el umbral congelado
  marca {agosto_alto} días de agosto de {agosto_dias}: hay que recalibrar, o leer cada día contra
  los catorce anteriores.
- **El libro de averías es un dato con huecos**, y el modelo se juzga contra él.
- **Detectar no es avisar**: el umbral del {detectados} de {sucesos} salta con el compresor casi a
  tope, así que constata un desastre en curso.
- **Un PostgreSQL portátil no es una base de producción**: sin copias automáticas, sin usuarios y
  sin nada que lo sostenga si se cae.

## Cómo comprobarlo

Cada cifra de este folio sale de correr un script, y diez comprobaciones se ponen entre una
lección y un commit. El curso son {modulos} módulos, el panel enseña los {dias_panel} días, y el
código está en **github.com/kmortizva-data/fuelle**.
