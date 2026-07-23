"""Local-redirect OAuth2 authorization-code capture.

Opens the browser to `authorize_url`, listens on 127.0.0.1:`port` for the
provider's redirect, and returns the `code` query param. Same pattern as
`gcloud auth login` / most CLI OAuth flows — nothing but the code touches
this machine's loopback interface.
"""
from __future__ import annotations

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


def capture_code(authorize_url: str, port: int, timeout_s: int = 180) -> str:
    result: dict[str, str] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — required by BaseHTTPRequestHandler
            qs = parse_qs(urlparse(self.path).query)
            if "code" in qs:
                result["code"] = qs["code"][0]
                body = b"<html><body>Connected. You can close this tab.</body></html>"
            else:
                result["error"] = qs.get("error", ["unknown_error"])[0]
                body = b"<html><body>Authorization failed. Check the terminal.</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)
            done.set()

        def log_message(self, *args):  # silence default stderr logging
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    webbrowser.open(authorize_url)
    print(f"Opened browser for login. Waiting on http://127.0.0.1:{port}/callback ...")

    if not done.wait(timeout_s):
        server.server_close()
        raise TimeoutError("Timed out waiting for OAuth redirect.")
    server_thread.join(timeout=2)

    if "error" in result:
        raise RuntimeError(f"OAuth provider returned error: {result['error']}")
    return result["code"]
