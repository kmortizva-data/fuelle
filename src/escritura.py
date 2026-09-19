"""How this project writes a Parquet so that two runs give the same bytes.

Found by module 29, the first time the whole lake was deleted and rebuilt. The
same rows came back, but not the same files: DuckDB writes a partitioned COPY
with several threads at once, each thread cuts its own files, and which rows
land in which file, in which order, changes from one run to the next. In bronze
198 files out of 212 came back identical; in silver, none did, and even the
number of files changed, 404 against 414.

That looks harmless, since the content is the same, and it is not. A floating
point average summed in a different order changes in its last digit, and when
it falls exactly on the half of a rounding it goes one way or the other: five
hours out of 4,416 in `oro_horas` moved by a hundredth. The compressed size of
each column moves too, and module 7 publishes those bytes.

Two causes, which src/orchestration/hilos.py separates. **Row order** decides the
averages and most of the size: the old silver came out in a scrambled order,
and writing it in time order alone gives back the averages and takes it from
about 24 MB to 21.88. **Threads** decide whether the bytes repeat: with several,
even sorted, a few files still differ from one run to the next. With one thread
they come out identical, for about two seconds more.
"""

from __future__ import annotations

import contextlib

import duckdb


@contextlib.contextmanager
def un_solo_hilo(con: duckdb.DuckDBPyConnection):
    """Lo de dentro corre con un solo hilo, y la conexión vuelve a como estaba."""
    antes = con.sql("SELECT current_setting('threads')").fetchone()[0]
    con.execute("SET threads = 1")
    try:
        yield
    finally:
        con.execute(f"SET threads = {antes}")
