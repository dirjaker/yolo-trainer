"""YOLO Trainer 前端 Web 服务器 — 端口 10001，代理 /api/v1/ → 127.0.0.1:10003"""
import http.server
import os
import urllib.request
import urllib.error
import socketserver

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
API_BASE = "http://127.0.0.1:10003"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def _proxy(self):
        url = API_BASE + self.path
        data = None
        if self.command in ("POST", "PUT", "PATCH"):
            length = int(self.headers.get("Content-Length", 0))
            if length:
                data = self.rfile.read(length)
        req = urllib.request.Request(url, data=data, method=self.command)
        for h in ("Authorization", "Content-Type", "Accept"):
            if h in self.headers:
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(e.read())

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy()
        path = self.path.split("?")[0]
        if path == "/" or not os.path.exists(os.path.join(DIST_DIR, path.lstrip("/"))):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        return self._proxy() if self.path.startswith("/api/") else self.send_error(404)

    def do_PUT(self):
        return self._proxy() if self.path.startswith("/api/") else self.send_error(404)

    def do_DELETE(self):
        return self._proxy() if self.path.startswith("/api/") else self.send_error(404)

    def do_PATCH(self):
        return self._proxy() if self.path.startswith("/api/") else self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept")
        self.end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", 10001), ProxyHandler)
    print("YOLO Trainer Web 服务器已启动 → http://0.0.0.0:10001")
    httpd.serve_forever()
