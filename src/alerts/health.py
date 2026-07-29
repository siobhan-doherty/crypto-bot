"""
Health check endpoint for alert service.
"""
import json
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler responding to /health and /ready endpoints."""
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._send_response(200, {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})
        elif self.path == "/ready":
            # for readiness probes
            self._send_response(200, {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()})
        else:
            self._send_response(404, {"error": "Not found"})


    def _send_response(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def start_health_server(port: int = 8080):
    """Start health check server in background thread."""
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()
