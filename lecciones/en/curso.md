## What this is

An air compressor on a Porto Metro train logged fifteen signals every ten seconds for seven
months. Inside that record there are **four real failures**, each with its date and its
maintenance report, and every one of them was an air leak.

This course builds two things around that archive. First the **data lake**: how a 208 MB file is
brought in without breaking it, how it is stored so it answers quickly, and how it is questioned
in SQL. Then the **digital twin**: a model of the compressor's physics running alongside the
original, whose disagreement with reality gives the leak away.

It starts without knowing what a table is.

## Why a compressor

Because compressed air is what feeds the flotation columns of a plant, and because a leak in the
air line is lost recovery without any alarm noticing.

And for something this project will repeat to the end: **pressure does not drop when there is a
leak**, because the control loop holds it. What rises is how hard the compressor has to work to
hold it. Watching the wrong variable is seeing nothing.

## How it is made

Every figure in a lesson came from running its script against the real data. None is copied from
somewhere else or rounded to look neat. When a number disagrees with what was expected, the
lesson says so instead of adjusting it.

The SQL lessons are not read, they are touched. The query runs inside your browser, against the
compressor's data, and the challenge at the end checks your answer.

## The data

**MetroPT-3**, from the University of California Irvine repository, licensed CC BY 4.0. Davari,
Veloso, Ribeiro and Gama (2021), [doi.org/10.24432/C5VW3R](https://doi.org/10.24432/C5VW3R).
