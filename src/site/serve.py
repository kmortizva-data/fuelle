"""Servidor local que se parece a GitHub Pages, en vez de a un cuello de botella.

`python -m http.server` sirve en un solo hilo y sin comprimir. Midiéndolo aquí,
tardó 19 segundos en entregar el worker de 0,69 MB, así que el wasm de 34 MB
habría tardado un cuarto de hora y la prueba habría medido el servidor en vez de
la página.

Este hace las dos cosas que hace Pages y aquel no:

  - Sirve en varios hilos, así que el navegador puede pedir en paralelo.
  - Comprime con gzip lo que Pages comprime, incluido `application/wasm`. Eso se
    comprobó contra un wasm real servido desde Pages, que vuelve con
    Content-Encoding: gzip.

Así el tiempo de carga que se mide aquí se parece al que verá un lector, que es
la cifra que la lección publica.

Correr:  .venv\\Scripts\\python.exe src\\site\\serve.py [puerto]
"""

from __future__ import annotations

import gzip
import io
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]

# Lo que GitHub Pages comprime. El wasm entra: verificado contra Pages, no supuesto.
COMPRESSIBLE = {
    ".html", ".css", ".json", ".svg", ".txt", ".md", ".wasm",
}
# `.js` y `.mjs` NO se comprimen aquí, a diferencia de Pages. No es por
# corrección: en esta máquina, servir un `.js` grande se lleva 19 segundos fijos,
# comprimido o no, porque algo local escanea el JavaScript. Comprimirlos solo
# añadía trabajo sin quitar la espera. Producción sí los sirve comprimidos.
MIN_COMPRESS_BYTES = 1024

# Comprimir 34 MB de wasm cuesta segundos de CPU, y sin esto se pagaban en CADA
# petición: la primera prueba se quedó colgada por eso, y el diagnóstico apuntaba
# a la red cuando el culpable era el servidor. Se guarda por fichero y fecha, así
# que editar un fichero invalida su entrada.
_CACHE: dict[tuple[str, float, int], bytes] = {}


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".mjs": "text/javascript",
        ".parquet": "application/vnd.apache.parquet",
        ".woff2": "font/woff2",
    }

    def end_headers(self):
        # En desarrollo la caché estorba: se edita un fichero y el navegador
        # sirve el viejo. Pero los ficheros de terceros de assets/ sí se cachean,
        # y esto costó una tarde de diagnóstico:
        #
        # sin caché, el worker de DuckDB se volvía a pedir en cada recarga, cada
        # petición se llevaba los 19 segundos fijos del escáner local, y el
        # navegador ABORTABA el arranque del Worker por tardar demasiado. El
        # síntoma era "ERROR: error" sin más detalle, que no apunta a nada.
        # Con caché arranca a la primera.
        if "/assets/" not in self.path:
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_dir() or not path.is_file():
            return super().send_head()

        stat = path.stat()
        accepts_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
        big_enough = stat.st_size >= MIN_COMPRESS_BYTES
        if not (accepts_gzip and big_enough and path.suffix.lower() in COMPRESSIBLE):
            return super().send_head()

        key = (str(path), stat.st_mtime, stat.st_size)
        body = _CACHE.get(key)
        if body is None:
            body = gzip.compress(path.read_bytes(), 6)
            # Se guarda lo que cuesta caro de comprimir. Lo pequeño se recomprime
            # sin que se note, y así la caché no crece sin control ni sirve nada
            # rancio tras editar un fichero.
            if stat.st_size >= 256 * 1024:
                if len(_CACHE) > 8:
                    _CACHE.pop(next(iter(_CACHE)))
                _CACHE[key] = body

        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return io.BytesIO(body)

    def log_message(self, fmt, *args):
        pass  # el ruido de cada petición no aporta nada aquí


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8531
    handler = partial(Handler, directory=str(PROJECT))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Fuelle en http://localhost:{port}/  (raíz: {PROJECT.name}, gzip como Pages)")
    server.serve_forever()


if __name__ == "__main__":
    main()
