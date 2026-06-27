#!/usr/bin/env python3
"""YOLO Trainer 前端 + API 反向代理"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import os

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
API_BASE = "http://127.0.0.1:10003"

MIME = {
    ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
    ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
    ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff2": "font/woff2",
}


class Handler(BaseHTTPRequestHandler):
    def _proxy(self):
        try:
            url = f"{API_BASE}{self.path}"
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None

            req = urllib.request.Request(url, data=body, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "content-length", "connection"):
                    req.add_header(k, v)

            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                self.send_response(r.status)
                ct = r.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            body = f'{{"error":"{e}"}}'.encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def _static(self):
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        fpath = os.path.join(FRONTEND_DIR, path.lstrip("/"))
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                data = f.read()
            ext = os.path.splitext(fpath)[1]
            self.send_response(200)
            self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            # SPA fallback
            with open(os.path.join(FRONTEND_DIR, "index.html"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self._static()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"Frontend: {FRONTEND_DIR}")
    print(f"API proxy: {API_BASE}")
    HTTPServer(("0.0.0.0", 10001), Handler).serve_forever()
