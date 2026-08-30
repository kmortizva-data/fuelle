## Qué es esto

Un compresor de aire de un tren del Metro de Oporto estuvo registrando quince señales cada diez
segundos durante siete meses. En ese registro hay **cuatro averías reales**, con su fecha y su
parte de mantenimiento, y todas fueron fugas de aire.

Este curso construye dos cosas alrededor de ese archivo. Primero el **lago de datos**: cómo se
trae un fichero de 208 MB sin romperlo, cómo se guarda para que responda rápido, y cómo se le
pregunta en SQL. Después el **gemelo digital**: un modelo de la física del compresor que corre en
paralelo al original, y cuya discrepancia con la realidad delata la fuga.

Se empieza sin saber qué es una tabla.

## Por qué un compresor

Porque el aire comprimido alimenta las columnas de flotación de una planta. Y porque una fuga en
la red de aire es recuperación perdida sin que ninguna alarma se entere.

Y por algo que este proyecto va a repetir hasta el final: **la presión no baja cuando hay una
fuga**, porque el control la sostiene. Lo que sube es cuánto tiene que trabajar el compresor para
sostenerla. Mirar la variable equivocada es no ver nada.

## Cómo está hecho

Cada cifra que aparece en una lección salió de correr su script contra los datos reales. Ninguna
está copiada de otro sitio ni redondeada para que quede bonita. Cuando un número no cuadra con lo
que se esperaba, la lección lo dice en vez de ajustarlo.

Las lecciones de SQL no se leen: se tocan. La consulta se ejecuta dentro de tu navegador, contra
los datos del compresor, y el reto del final comprueba tu respuesta.

## Los datos

**MetroPT-3**, del repositorio de la Universidad de California en Irvine, con licencia CC BY 4.0.
Davari, Veloso, Ribeiro y Gama (2021), [doi.org/10.24432/C5VW3R](https://doi.org/10.24432/C5VW3R).
