from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


STATIC_ROOT = Path(__file__).resolve().parent
API_BASE_URL = os.environ.get("AIWM_API_BASE_URL", "http://api:8000").rstrip("/") + "/"
PORT = int(os.environ.get("AIWM_WEB_PORT", "8501"))

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class NarraStudioWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy_api()
            return
        super().do_GET()

    def do_POST(self):
        self._proxy_api_or_404()

    def do_PATCH(self):
        self._proxy_api_or_404()

    def do_PUT(self):
        self._proxy_api_or_404()

    def do_DELETE(self):
        self._proxy_api_or_404()

    def do_OPTIONS(self):
        self._proxy_api_or_404()

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _proxy_api_or_404(self):
        if self.path.startswith("/api/"):
            self._proxy_api()
            return
        self.send_error(404, "Not found")

    def _proxy_api(self):
        target_url = urljoin(API_BASE_URL, self.path.lstrip("/"))
        body = self._read_body()
        headers = self._proxy_headers()
        request = Request(target_url, data=body, headers=headers, method=self.command)

        try:
            with urlopen(request, timeout=120) as response:
                payload = response.read()
                self._send_proxy_response(response.status, response.headers, payload)
        except HTTPError as exc:
            self._send_proxy_response(exc.code, exc.headers, exc.read())
        except URLError as exc:
            payload = json.dumps(
                {
                    "error_type": "API_PROXY_ERROR",
                    "message": f"Web proxy could not reach backend API: {exc.reason}",
                }
            ).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _read_body(self) -> bytes | None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return None
        return self.rfile.read(length)

    def _proxy_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            lower = key.lower()
            if lower in HOP_BY_HOP_HEADERS or lower in {"host", "content-length"}:
                continue
            headers[key] = value
        headers["Host"] = API_BASE_URL.removeprefix("http://").removeprefix("https://").split("/", 1)[0]
        return headers

    def _send_proxy_response(self, status: int, response_headers, payload: bytes):
        self.send_response(status)
        for key, value in response_headers.items():
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            if key.lower() in {"content-length", "server", "date"}:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), NarraStudioWebHandler)
    print(f"Narra Studio web server listening on 0.0.0.0:{PORT}, proxying /api to {API_BASE_URL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
