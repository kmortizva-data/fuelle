"""Which results a figure was drawn from, so a stale PNG is caught by content.

The Spanish figure of module 21 showed 0.2943 s for two months while its JSON said
0.2925: the script was rerun, the English figure was redrawn, the Spanish one was not,
and no gate compared a PNG with the numbers it is supposed to draw.

The obvious guard, "no PNG older than its JSON", compares dates, and dates lie here:
the module 29 rebuild rewrote two dozen JSON files with identical content, so a date
guard accuses 24 correct figures. This one compares content instead. Every run of a
figure script records a recipe for each PNG it writes:

    the hash of the PNG itself, and the canonical hash of every results/*.json the
    script read while it ran.

The canonical hash parses the JSON and dumps it with sorted keys, so a CRLF checkout
or a reordered key does not count as a change. A figure is stale when any of those
hashes no longer matches the file on disk.

What it does not see: inputs that are not results/*.json (the lake for modules 1 and 2,
the dbt manifest for 17, the Dagster definitions for 29). Those figures are checked
for their PNG hash only.

This module imports no matplotlib, so the gate can use it without drawing anything.
"""

from __future__ import annotations

import atexit
import builtins
import hashlib
import io
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT / "results"
RECIPES = RESULTS / "figuras_fuentes.json"

# Written by the figure scripts themselves, never read as an input to a drawing.
OUTPUTS = {"figuras.json", RECIPES.name}

_read: set[Path] = set()
_written: dict[str, Path] = {}
_installed = False


def canonical_hash(path: Path) -> str:
    """The hash of what a JSON says, not of how its bytes happen to be laid out."""
    data = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _note_read(file, mode) -> None:
    if "r" not in str(mode) or any(m in str(mode) for m in "wa+"):
        return
    try:
        path = Path(file).resolve()
    except TypeError:
        return
    if path.parent == RESULTS and path.suffix == ".json" and path.name not in OUTPUTS:
        _read.add(path)


def note_written(path: Path) -> None:
    """Called by the savefig hook with the file actually written."""
    path = Path(path).resolve()
    _written[path.name] = path


def install() -> None:
    """Start recording. Idempotent; figures_theme calls it once per process."""
    global _installed
    if _installed:
        return
    original_open = builtins.open

    def recording_open(file, mode="r", *args, **kwargs):
        _note_read(file, mode)
        return original_open(file, mode, *args, **kwargs)

    # pathlib goes through io.open and the scripts call both, so both are patched.
    builtins.open = recording_open
    io.open = recording_open
    atexit.register(_save)
    _installed = True


def load() -> dict:
    if not RECIPES.exists():
        return {}
    return json.loads(RECIPES.read_text(encoding="utf-8"))


def _save() -> None:
    if not _written:
        return
    inputs = {p.name: canonical_hash(p) for p in sorted(_read) if p.exists()}
    recipes = load()
    for name, path in _written.items():
        if path.exists():
            recipes[name] = {"png": file_hash(path), "fuentes": inputs}
    RECIPES.write_text(
        json.dumps(dict(sorted(recipes.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def stale(png: Path, recipes: dict | None = None) -> list[str]:
    """Why this PNG no longer matches what it was drawn from. Empty when it does."""
    recipes = load() if recipes is None else recipes
    recipe = recipes.get(png.name)
    if recipe is None:
        return [f"{png.name} no tiene receta"]
    problems = []
    if file_hash(png) != recipe["png"]:
        problems.append(f"{png.name} no es el PNG que dibujó su script")
    for name, wanted in recipe["fuentes"].items():
        source = RESULTS / name
        if not source.exists():
            problems.append(f"{png.name} sale de {name}, que ya no existe")
        elif canonical_hash(source) != wanted:
            problems.append(f"{png.name} se dibujó con otro {name}")
    return problems
