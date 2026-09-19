## Cómo se lee

La línea continua es el compresor de verdad: las horas que lleva cargando aire, sumadas a lo largo
del día. Un compresor sano carga poco y a ratos, así que su línea apenas se levanta del suelo.

La línea discontinua es el gemelo, un modelo de la misma máquina hecho con cuatro números medidos
en febrero. Dice cuánto habría cargado la máquina sana con el consumo normal de la planta, durante
las mismas horas que hay registradas.

La franja es la zona sana. Hasta ahí llegaría una máquina que pasara el día entero como en su hora
más cargada de febrero. Una línea continua que se sale de la franja es un compresor trabajando
para alimentar algo que no es la planta: una fuga.

Las rayas verticales marcan cuándo salta la alarma y cuándo empieza o se cierra un parte de
avería. Las zonas rayadas son horas sin registro, y ahí las dos líneas se quedan quietas porque no
hay nada que medir.

La alarma es la del veredicto. Salta cuando en alguna hora la planta gasta 1,15 bar por minuto más
de lo que gastaba sana. Es el umbral más alto con el que el gemelo todavía pilla las cuatro averías
documentadas.

## De dónde sale

Cada día de este panel se calculó antes, en Python, y la página solo elige cuál enseñar. Por eso
contesta al instante y no necesita ningún servidor: los 214 días viajan juntos en un solo fichero.

El veredicto completo, con sus dos cuentas y el rival que la máquina ya traía puesto, está en el
[módulo 28](m28_veredicto.html). Cómo se construyó esta página, y por qué no tiene servidor, en el
[módulo 30](m30_panel.html). Todo el código está en
[GitHub](https://github.com/kmortizva-data/fuelle).

Los datos son MetroPT-3, del repositorio de la UCI, con licencia CC BY 4.0. Davari, Veloso,
Ribeiro y Gama (2021), [doi.org/10.24432/C5VW3R](https://doi.org/10.24432/C5VW3R).
