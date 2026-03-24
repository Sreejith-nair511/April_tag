"""
Lightweight web monitoring server for the Precision Landing System.
Uses only Python stdlib (http.server + json). No Flask or extra dependencies.
Runs in its own daemon thread alongside the pipeline.
"""
import os
import sys
import json
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import setup_logger  # type: ignore[import]

logger = setup_logger("WebServer")

# Shared state dictionary updated by the pipeline
_status_lock = threading.Lock()
_history: List[Dict[str, float]] = []

_system_status: Dict[str, Any] = {
    "timestamp": 0,
    "fps": 0.0,
    "landing_state": "IDLE",
    "camera_ok": False,
    "mavlink_ok": False,
    "tracking_active": False,
    "marker_x": 0.0,
    "marker_y": 0.0,
    "marker_z": 0.0,
}

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def update_status(data: Dict[str, Any]) -> None:
    """Thread-safe update of the shared status dict."""
    with _status_lock:
        _system_status.update(data)
        _system_status["timestamp"] = time.time()
        # Keep a rolling history of marker positions (max 50)
        if data.get("marker_x") is not None:
            _history.append({
                "x": float(data.get("marker_x", 0)),
                "y": float(data.get("marker_y", 0)),
                "z": float(data.get("marker_z", 0)),
                "t": time.time()
            })
            while len(_history) > 50:
                _history.pop(0)


def get_status() -> Dict[str, Any]:
    with _status_lock:
        result = dict(_system_status)
        result["history"] = list(_history)
        return result


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves the static dashboard and a /api/status JSON endpoint."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/status":
            self._send_json(get_status())
            return

        # Serve static files (index.html, etc.)
        super().do_GET()

    def _send_json(self, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default HTTP logs to avoid spamming the console
        pass


class WebMonitorServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        server = HTTPServer((self.host, self.port), DashboardHandler)
        self.server = server
        thread = threading.Thread(target=server.serve_forever, name="WebMonitor")
        thread.daemon = True
        thread.start()
        self.thread = thread
        logger.info(f"Web dashboard running at http://{self.host}:{self.port}")

    def stop(self) -> None:
        server = self.server
        if server is not None:
            server.shutdown()
            logger.info("Web dashboard stopped.")
