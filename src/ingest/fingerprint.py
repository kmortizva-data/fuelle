"""Running it twice: the experiment, not the claim. Module 5.

`bronze.py` says it is idempotent and it is, but it gets there the cheap way: it
deletes the folder and writes it again. That hides the failure this module is
about. A pipeline that APPENDS is the normal shape of the thing, and it will
duplicate everything on a rerun without a single error message.

So this script runs three experiments and publishes the numbers:

  1. **The naive pipeline.** Ingest three times, appending. The row count has to
     triple. If it did not, there would be nothing to teach here.
  2. **The guarded pipeline.** The same three runs, with a fingerprint of the
     source stored next to the data. Runs two and three do nothing, and the
     count does not move.
  3. **The fingerprint has to be able to change.** A fingerprint that has never
     been seen changing proves nothing: it could be returning a constant. So one
     single byte of a copy of the source gets flipped, and both the hash and the
     pipeline's decision are measured again.

The third is the one that makes the other two mean something, and it is the one
almost every tutorial leaves out.

Run:  .venv\\Scripts\\python.exe src\\ingest\\fingerprint.py
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_huella"
RESULTS = PROJECT / "results" / "m05_fingerprint.json"

RUNS_OF_THE_EXPERIMENT = 3


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with io.open(path, "rb") as fh:
        while block := fh.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def bits_apart(a: str, b: str) -> int:
    """How many of the 256 bits differ between two hashes.

    A hash that changed in only a couple of bits would be a bad hash: a single
    edited byte is supposed to scramble the whole thing. This measures that
    instead of taking it on faith.
    """
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def naive_ingest(con: duckdb.DuckDBPyConnection, target: Path, part: int) -> None:
    """The pipeline almost everyone writes first: it appends and never checks.

    Each run drops its output in a new file, which is exactly what a daily job
    writing `telemetria_<date>.parquet` does. Nothing here is wrong on its own.
    The bug only appears the second time it runs on the same input.
    """
    target.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"COPY (SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')) "
        f"TO '{(target / f'run_{part}.parquet').as_posix()}' "
        f"(FORMAT PARQUET, COMPRESSION ZSTD)"
    )


def guarded_ingest(con: duckdb.DuckDBPyConnection, target: Path, part: int,
                   source: Path, manifest: Path) -> bool:
    """The same thing, with one question asked first: has the source changed?

    Returns whether it actually ingested. The fingerprint is stored beside the
    data, so the answer survives the process ending, the machine rebooting and
    the person who wrote it leaving the company.
    """
    current = sha256_of(source)
    if manifest.exists():
        seen = json.loads(io.open(manifest, encoding="utf-8").read())
        if seen.get("source_sha256") == current:
            return False

    naive_ingest(con, target, part)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with io.open(manifest, "w", encoding="utf-8") as fh:
        json.dump({"source_sha256": current, "source_bytes": source.stat().st_size},
                  fh, ensure_ascii=False, indent=2)
    return True


def count(con: duckdb.DuckDBPyConnection, target: Path) -> int:
    if not any(target.glob("*.parquet")):
        return 0
    return con.sql(
        f"SELECT count(*) FROM read_parquet('{target.as_posix()}/*.parquet')").fetchone()[0]


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    truth = con.sql(
        f"SELECT count(*) FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')").fetchone()[0]
    print(f"The source holds {truth:,} rows. Every run below ingests that same source.")
    print()

    # --- 1. The naive pipeline, run three times ---------------------------
    naive_dir = SCRATCH / "naive"
    naive_counts = []
    for run in range(1, RUNS_OF_THE_EXPERIMENT + 1):
        naive_ingest(con, naive_dir, run)
        naive_counts.append(count(con, naive_dir))
        print(f"  naive    run {run}: {naive_counts[-1]:>10,} rows")

    # --- 2. The guarded pipeline, run three times -------------------------
    guarded_dir = SCRATCH / "guarded"
    manifest = SCRATCH / "guarded_manifest.json"
    guarded_counts, ingested = [], []
    for run in range(1, RUNS_OF_THE_EXPERIMENT + 1):
        did = guarded_ingest(con, guarded_dir, run, RAW_CSV, manifest)
        ingested.append(did)
        guarded_counts.append(count(con, guarded_dir))
        print(f"  guarded  run {run}: {guarded_counts[-1]:>10,} rows   "
              f"{'ingested' if did else 'skipped, source unchanged'}")

    # --- 3. One byte, and the fingerprint has to notice -------------------
    print()
    copy = SCRATCH / "copia.csv"
    print("Copying the source to flip one byte of it...")
    shutil.copy2(RAW_CSV, copy)
    total_bytes = copy.stat().st_size

    before = sha256_of(copy)
    position = total_bytes // 2
    with io.open(copy, "r+b") as fh:
        fh.seek(position)
        original_byte = fh.read(1)
        # Any different byte will do. Digits stay digits so the file still
        # parses: the point is that a change no reader would notice is still a
        # change the fingerprint cannot miss.
        new_byte = b"7" if original_byte != b"7" else b"3"
        fh.seek(position)
        fh.write(new_byte)
    after = sha256_of(copy)

    differing = bits_apart(before, after)
    print(f"  byte {position:,} of {total_bytes:,}: "
          f"{original_byte.decode('latin-1')!r} -> {new_byte.decode('latin-1')!r}")
    print(f"  before  {before}")
    print(f"  after   {after}")
    print(f"  {differing} of 256 bits in the hash changed")

    # And the pipeline has to act on it: same manifest, changed source.
    changed_manifest = SCRATCH / "changed_manifest.json"
    shutil.copy2(manifest, changed_manifest)
    reacted = guarded_ingest(con, SCRATCH / "after_change", 1, copy, changed_manifest)
    print(f"  the guarded pipeline ingests again: {reacted}")

    hashing = measure(lambda: sha256_of(copy), runs=5)
    speed = total_bytes / 1024 / 1024 / hashing.median

    payload = {
        "filas_origen": truth,
        "corridas_del_experimento": RUNS_OF_THE_EXPERIMENT,
        "filas_naive_por_corrida": naive_counts,
        "filas_naive_al_final": naive_counts[-1],
        "veces_duplicado": round(naive_counts[-1] / truth, 2),
        "filas_guarded_por_corrida": guarded_counts,
        "filas_guarded_al_final": guarded_counts[-1],
        "corridas_que_ingirieron": sum(ingested),
        "bytes_del_fichero": total_bytes,
        "byte_cambiado": position,
        "sha_antes": before,
        "sha_despues": after,
        "bits_distintos_de_256": differing,
        "por_ciento_de_bits_distintos": round(differing / 256 * 100, 1),
        "reingirio_tras_el_cambio": reacted,
        "huella_segundos": round(hashing.median, 2),
        "huella_mb_s": round(speed),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  naive after {RUNS_OF_THE_EXPERIMENT} runs: {naive_counts[-1]:,} rows "
          f"({payload['veces_duplicado']}x the truth)")
    print(f"  guarded after {RUNS_OF_THE_EXPERIMENT} runs: {guarded_counts[-1]:,} rows "
          f"({sum(ingested)} of {RUNS_OF_THE_EXPERIMENT} runs did any work)")
    print(f"Written to {RESULTS.relative_to(PROJECT)}")

    shutil.rmtree(SCRATCH, ignore_errors=True)

    # The three things this experiment must show, checked instead of assumed.
    if naive_counts[-1] != truth * RUNS_OF_THE_EXPERIMENT:
        raise SystemExit("The naive pipeline did not duplicate. The demo is broken.")
    if guarded_counts[-1] != truth:
        raise SystemExit("The guarded pipeline moved the count. That is the bug it prevents.")
    if not reacted:
        raise SystemExit("The fingerprint did not notice a changed byte. It is useless.")


if __name__ == "__main__":
    main()
