"""
Local authenticated proxy for Cloud Run.
Runs on http://localhost:8080 and forwards all requests to Cloud Run
with a valid identity token injected automatically.

Usage:
    python3 local_proxy.py
Then open: http://localhost:8080/docs
"""
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

CLOUD_RUN_URL = "https://promogen-73298798964.us-central1.run.app"
LOCAL_PORT = 8080

_token_cache = {"token": None}
_token_lock = threading.Lock()


def get_token():
    with _token_lock:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True, text=True
        )
        token = result.stdout.strip()
        _token_cache["token"] = token
        return token


class ProxyHandler(BaseHTTPRequestHandler):
    def do_request(self):
        token = get_token()
        target = f"{CLOUD_RUN_URL}{self.path}"

        body = None
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length:
            body = self.rfile.read(content_length)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": self.headers.get("Content-Type", "application/json"),
        }

        req = Request(target, data=body, headers=headers, method=self.command)
        try:
            with urlopen(req) as resp:
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in ("transfer-encoding",):
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_request

    def log_message(self, format, *args):
        print(f"  {self.path}  →  {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print(f"Fetching identity token...")
    get_token()
    print(f"Proxy running at http://localhost:{LOCAL_PORT}")
    print(f"Swagger UI  →  http://localhost:{LOCAL_PORT}/docs")
    print(f"ReDoc       →  http://localhost:{LOCAL_PORT}/redoc")
    print("Press Ctrl+C to stop.\n")
    HTTPServer(("localhost", LOCAL_PORT), ProxyHandler).serve_forever()
