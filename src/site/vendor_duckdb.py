"""Bring DuckDB-Wasm into the site, with every dependency, and nothing left pointing outside.

The live query block runs DuckDB inside the reader's browser. Two ways to get it
there: load it from a CDN, or host it ourselves. This project hosts it.

Why self-host, decided on measurements taken 2026-08-30:
  - Silica and Geostatistics depend on nobody, and this course should not either.
  - The CDN saves about 1 MB over GitHub Pages on the wasm alone: 6.79 against
    7.88 MB, remeasured on 2026-09-18, because the CDN answers with brotli and
    Pages with gzip at level 5. Not worth a runtime dependency on a third party.
  - No reader IP addresses leak to someone else's server.
  - GitHub Pages DOES compress application/wasm: measured against a real wasm
    served from Pages, which came back with Content-Encoding: gzip. So the
    reader downloads about 8 MB, not the 34 MB sitting on disk.

The published ESM bundles import their dependencies by CDN path, so this script
walks that chain, downloads every module, and rewrites the imports to local
files. Nothing in assets/duckdb-wasm/ may point outside when it finishes, and
the check at the bottom fails if anything does.

These files are NOT in git (see .gitignore): they are 35 MB of somebody else's
build output. This script is how they come back.

Run:  .venv\\Scripts\\python.exe src\\site\\vendor_duckdb.py
"""

from __future__ import annotations

import gzip
import json
import io
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
VENDOR = PROJECT / "assets" / "duckdb-wasm"

CDN = "https://cdn.jsdelivr.net"
DUCKDB_VERSION = "1.33.1-dev57.0"

# The two files that are not ES modules and are fetched by name at runtime.
BINARIES = {
    "duckdb-eh.wasm": f"/npm/@duckdb/duckdb-wasm@{DUCKDB_VERSION}/dist/duckdb-eh.wasm",
    "duckdb-browser-eh.worker.js":
        f"/npm/@duckdb/duckdb-wasm@{DUCKDB_VERSION}/dist/duckdb-browser-eh.worker.js",
}

ENTRY = f"/npm/@duckdb/duckdb-wasm@{DUCKDB_VERSION}/+esm"
IMPORT_PATTERN = re.compile(r'(?:from|import)"(/npm/[^"]+)"')


def fetch(path: str) -> bytes:
    request = urllib.request.Request(
        CDN + path, headers={"User-Agent": "fuelle-vendor/1.0"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def local_name(cdn_path: str) -> str:
    """/npm/apache-arrow@17.0.0/+esm  ->  apache-arrow.mjs"""
    package = cdn_path.removeprefix("/npm/").split("/+esm")[0]
    package = package.rsplit("@", 1)[0] if "@" in package[1:] else package
    return package.replace("/", "-").lstrip("-") + ".mjs"


def vendor_modules() -> dict[str, str]:
    """Walk the import chain, saving every module and rewriting its imports."""
    queue = [(ENTRY, "duckdb.mjs")]
    seen: dict[str, str] = {}

    while queue:
        cdn_path, filename = queue.pop()
        if cdn_path in seen:
            continue
        seen[cdn_path] = filename

        source = fetch(cdn_path).decode("utf-8")
        for dependency in set(IMPORT_PATTERN.findall(source)):
            name = local_name(dependency)
            if dependency not in seen:
                queue.append((dependency, name))
            source = source.replace(f'"{dependency}"', f'"./{name}"')

        (VENDOR / filename).write_text(source, encoding="utf-8")
        print(f"  {filename:<28} {len(source)/1024:>8.1f} KB")

    return seen


LICENCE_NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md")


def licence_text(package: str) -> tuple[bytes | None, str]:
    """A package's licence, and where it came from.

    First from the npm package itself, at the vendored version. Some packages
    declare their licence in package.json and ship no text: @duckdb/duckdb-wasm
    is one, it says MIT and brings no LICENSE file. For those, the text comes
    from the repository the package itself declares on npm, and the file says
    so in its first line, so nobody mistakes it for a copy from the package.
    """
    for candidate in LICENCE_NAMES:
        try:
            return fetch(f"{package}/{candidate}"), f"npm {package}/{candidate}"
        except Exception:
            continue

    spec = package.removeprefix("/npm/")
    name, version = spec.rsplit("@", 1)
    registry = f"https://registry.npmjs.org/{name.replace('/', '%2f')}/{version}"
    try:
        with urllib.request.urlopen(registry, timeout=60) as response:
            meta = json.load(response)
    except Exception:
        return None, ""
    repo = (meta.get("repository") or {}).get("url", "")
    match = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", repo)
    if not match:
        return None, ""
    owner, project = match.groups()
    for candidate in LICENCE_NAMES:
        try:
            return (fetch(f"/gh/{owner}/{project}/{candidate}"),
                    f"github {owner}/{project}/{candidate} (declared licence: "
                    f"{meta.get('license')}; the npm package ships no text)")
        except Exception:
            continue
    return None, ""


def main() -> None:
    VENDOR.mkdir(parents=True, exist_ok=True)

    print("Modules (the import chain, rewritten to local files):")
    modules = vendor_modules()

    print("Binaries (fetched by name at runtime, not imported):")
    for filename, path in BINARIES.items():
        target = VENDOR / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"  {filename:<28} {target.stat().st_size/1048576:>8.2f} MB  (ya estaba)")
            continue
        data = fetch(path)
        target.write_bytes(data)
        print(f"  {filename:<28} {len(data)/1048576:>8.2f} MB")

    (VENDOR / "VERSION").write_text(DUCKDB_VERSION + "\n", encoding="utf-8")

    # The licences travel with the code. These files get published on a public
    # site, and two of the four packages are Apache 2.0, which requires a copy of
    # the licence with any redistribution. Each one is fetched from the exact
    # version that was vendored, so the text matches the code beside it.
    print("Licences (one per vendored package, from its own version):")
    licences = VENDOR / "licenses"
    licences.mkdir(exist_ok=True)
    packages = {f"/npm/@duckdb/duckdb-wasm@{DUCKDB_VERSION}"}
    packages |= {path.split("/+esm")[0] for path in modules}
    for package in sorted(packages):
        name = (package.removeprefix("/npm/").rsplit("@", 1)[0]
                .replace("/", "-").lstrip("@-"))
        text, source = licence_text(package)
        if text is None:
            raise SystemExit(f"No licence found for {package}. Do not publish without it.")
        (licences / f"{name}.txt").write_bytes(
            f"Source: {source}\n\n".encode("utf-8") + text)
        print(f"  {name:<28} {source}")

    # The gate: nothing may still point at the CDN.
    escapes = []
    for module in VENDOR.glob("*.mjs"):
        text = module.read_text(encoding="utf-8", errors="replace")
        for hit in IMPORT_PATTERN.findall(text):
            escapes.append(f"{module.name} -> {hit}")

    total_raw = total_gz = 0
    print()
    print("What the reader actually pays for:")
    for f in sorted(VENDOR.iterdir()):
        # The licences are a folder, and the reader never downloads them.
        if f.name == "VERSION" or f.is_dir():
            continue
        raw = f.stat().st_size
        gz = len(gzip.compress(f.read_bytes(), 6))
        total_raw += raw
        total_gz += gz
        print(f"  {f.name:<28} {raw/1048576:>7.2f} MB on disk   {gz/1048576:>6.2f} MB over the wire")
    print(f"  {'TOTAL':<28} {total_raw/1048576:>7.2f} MB on disk   {total_gz/1048576:>6.2f} MB over the wire")
    print()
    print(f"  {len(modules)} modules vendored, {len(BINARIES)} binaries.")

    if escapes:
        print()
        for escape in escapes:
            print(f"  STILL POINTING OUTSIDE: {escape}")
        raise SystemExit("Vendoring incomplete: something still loads from the CDN.")
    print("  Nothing points outside. The site is self-contained.")


if __name__ == "__main__":
    main()
