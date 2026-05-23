import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)


def run_health_server(port=8001):
    server = HTTPServer(("0.0.0.0", port), HealthHandler)  # nosec
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
