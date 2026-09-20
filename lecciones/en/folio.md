# The verdict, on one page

## The question

Does a model of a compressor's physics, calibrated on one healthy month and never shown a
failure, warn about air leaks better than the alarm the machine already carries?

## The method, in five lines

1. **{lecturas} readings** of {senales} signals, one every ten seconds, seven months of the air
   compressor of a Porto Metro train: {mb_csv} MB of CSV, from the UCI, under a CC BY 4.0 licence.
2. A **layered data lake**, with the readings laid on a regular ten second grid, and the same
   readings served from PostgreSQL too.
3. **Four numbers measured in February** describe the machine. It starts at {arranca} bar, stops
   at {para}, fills at {llena} bar per minute and the plant draws {consumo}. The air going in and
   the air going out balance to {descuadre} %.
4. The **twin** runs alongside with those four numbers frozen. The only thing anyone looks at is
   its disagreement with the machine, the **residual**, in bar per minute.
5. The threshold is not chosen: it is **swept whole**. The highest one that still catches the
   four documented failures is {umbral} bar per minute.

## The verdict

| Over the {dias_juzgados} days the twin can judge | The twin | The alarm fitted |
|---|---|---|
| Failures detected | **{detectados} of {sucesos}** | {lps_detectados} of {sucesos} |
| Days with an alarm | {dias_alarma} | {lps_dias} |
| False alarms a month | **{falsas_mes}** | {lps_falsas_mes} |

**What it does not do: predict.** Only one of the four warns beforehand, and by a single day. An
air leak does not grow slowly: it opens, and the compressor goes from working a twentieth of the
time to never stopping in a few hours.

**What it found without being asked.** Twelve days of March with the machine failing and no
maintenance report, and four independent signals say so at once. Counting March as a failure, the
result is {marzo_detectados} of {marzo_sucesos} at {marzo_falsas} false alarms a month.

## What would break in a real plant

- **One machine only.** The four numbers belong to this compressor; another one needs them
  measured again, and one healthy month is enough.
- **Four failures are not a sample.** This is a study of four cases, and one hit more or less
  moves the result.
- **Without the receiver's volume there are no litres.** The residual is in bar per minute, and
  turning it into a flow rate needs a number the datasheet does not give.
- **No reference leak.** Nobody opened a valve of known size, so the scale of severity is not
  calibrated.
- **The machine drifts.** Healthy demand doubles between February and August, and the frozen
  threshold marks {agosto_alto} days of August out of {agosto_dias}: it needs recalibrating, or
  reading each day against the fourteen before it.
- **The failure log is data with holes too**, and the model is judged against it.
- **Detecting is not warning**: the threshold that gets {detectados} of {sucesos} fires with the
  compressor almost flat out, so it states a disaster already under way.
- **A portable PostgreSQL is not a production database**: no automatic backups, no users, and
  nothing holding it up if it falls over.

## How to check it

Every number on this page comes out of running a script, and ten checks stand between a lesson
and a commit. The course is {modulos} modules, the panel shows the {dias_panel} days, and the
code is all at **github.com/kmortizva-data/fuelle**.
