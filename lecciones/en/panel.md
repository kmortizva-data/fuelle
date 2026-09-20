## How to read it

The solid line is the real compressor: the hours it has spent loading air, added up through the
day. A healthy compressor loads little and in short bursts, so its line barely lifts off the floor.

The dashed line is the twin, a model of the same machine built from four numbers measured in
February. It says how long the healthy machine would have loaded with the plant's normal demand,
over the same hours the record holds.

The band is the healthy zone. That is as far as a machine would get if it spent the whole day
like its busiest hour in February. A solid line leaving the band is a compressor working to feed
something that is not the plant: a leak.

The vertical lines mark when the alarm fires and when a failure report opens or closes. The
hatched stretches are hours with no record, and there both lines stay flat because there is
nothing to measure.

The alarm is the verdict's. It fires when, in some hour, the plant draws 1.15 bar per minute more
than it drew when healthy. That is the highest threshold at which the twin still catches all four
documented failures.

## Where it comes from

Every day on this panel was worked out beforehand, in Python, and the page only chooses which one
to show. That is why it answers instantly and needs no server: all 214 days travel together in a
single file.

The full verdict, with its two counts and the rival the machine already carried, is in
[module 28](m28_veredicto.en.html). How this page was built, and why it has no server, is in
[module 30](m30_panel.en.html). All the code is on
[GitHub](https://github.com/kmortizva-data/fuelle).

The data is MetroPT-3, from the UCI repository, under a CC BY 4.0 licence. Davari, Veloso,
Ribeiro and Gama (2021), [doi.org/10.24432/C5VW3R](https://doi.org/10.24432/C5VW3R).
