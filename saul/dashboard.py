"""Operator dashboard: a live, turn-by-turn view of each call, served from the agent process.

- In-memory only. Nothing is written to disk (docs/compliance/data-handling.md). Restarting the
  process clears it. Phone numbers are masked to the last four digits.
- Stdlib HTTP server + Server-Sent Events, so there is no extra dependency and no build step.
- The agent calls `bus.emit(...)` from its hooks; browsers subscribe at /events.
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

logger = logging.getLogger("saul.dashboard")

STATIC_DIR = Path(__file__).parent / "static"
MAX_CALLS = 20  # keep the last N calls in memory


class CallState:
    def __init__(self, call_id: str, label: str, started_at: float) -> None:
        self.id = call_id
        self.label = label
        self.started_at = started_at
        self.ended_at: float | None = None
        self.phase = "greet"
        self.turns: list[dict[str, Any]] = []  # {id, role, text, ts, interrupted}
        self.case: dict[str, Any] | None = None
        self.advice: dict[str, Any] | None = None
        self.advice_provider: str | None = None
        self.safety: list[str] = []
        self.notes: list[dict[str, Any]] = []  # {ts, text}
        self.termination_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "phase": self.phase,
            "turns": self.turns,
            "case": self.case,
            "advice": self.advice,
            "advice_provider": self.advice_provider,
            "safety": self.safety,
            "notes": self.notes,
            "termination_reason": self.termination_reason,
        }


class Bus:
    """Thread-safe event bus and state store shared by the agent hooks and the HTTP server."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: dict[str, CallState] = {}
        self._order: list[str] = []
        self._subscribers: list[queue.Queue] = []
        self._seq = 0

    # -- state -------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"calls": [self._calls[c].to_dict() for c in self._order]}

    def get(self, call_id: str) -> CallState | None:
        with self._lock:
            return self._calls.get(call_id)

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
            self._order.clear()

    # -- events ------------------------------------------------------------

    def emit(self, call_id: str, kind: str, **data: Any) -> dict[str, Any]:
        """Apply an event to the call's state and broadcast it. Never raises."""
        ts = time.time()
        with self._lock:
            self._seq += 1
            event = {"seq": self._seq, "ts": ts, "call_id": call_id, "type": kind, **data}
            try:
                self._apply(event)
            except Exception:
                logger.exception("dashboard failed to apply event %s", kind)
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass
        return event

    def _apply(self, e: dict[str, Any]) -> None:
        kind = e["type"]
        if kind == "call_start":
            state = CallState(e["call_id"], e.get("label", "call"), e["ts"])
            self._calls[e["call_id"]] = state
            self._order.append(e["call_id"])
            while len(self._order) > MAX_CALLS:
                self._calls.pop(self._order.pop(0), None)
            return
        state = self._calls.get(e["call_id"])
        if state is None:
            state = CallState(e["call_id"], e.get("label", "call"), e["ts"])
            self._calls[e["call_id"]] = state
            self._order.append(e["call_id"])
        if kind == "phase":
            state.phase = e["phase"]
            state.notes.append({"ts": e["ts"], "text": f"phase: {e['phase']}"})
        elif kind == "caller":
            turn_id = e.get("id") or f"c-{len(state.turns)}"
            e["id"] = turn_id
            for t in state.turns:
                if t["id"] == turn_id:
                    t["text"] = e["text"]
                    t["ts"] = e["ts"]
                    return
            state.turns.append({"id": turn_id, "role": "caller", "text": e["text"], "ts": e["ts"], "interrupted": False})
        elif kind == "agent":
            turn_id = f"a-{len(state.turns)}"
            e["id"] = turn_id
            state.turns.append(
                {"id": turn_id, "role": "agent", "text": e["text"], "ts": e["ts"], "interrupted": bool(e.get("interrupted"))}
            )
        elif kind == "case":
            state.case = e["case"]
        elif kind == "advice":
            state.advice = e["advice"]
            state.advice_provider = e.get("provider")
        elif kind == "safety":
            state.safety.append(e["category"])
            state.notes.append({"ts": e["ts"], "text": f"SAFETY: {e['category']}"})
        elif kind == "note":
            state.notes.append({"ts": e["ts"], "text": e["text"]})
        elif kind == "call_end":
            state.ended_at = e["ts"]
            state.termination_reason = e.get("reason")
            state.notes.append({"ts": e["ts"], "text": f"call ended: {e.get('reason')}"})

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=1000)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)


bus = Bus()


def mask_number(number: str | None) -> str:
    if not number:
        return "unknown number"
    digits = "".join(ch for ch in number if ch.isdigit())
    return f"•••-{digits[-4:]}" if len(digits) >= 4 else "unknown number"


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    server_version = "SaulDashboard/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002  keep the agent log quiet
        logger.debug("http: " + format, *args)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send_file(STATIC_DIR / "dashboard.html", "text/html; charset=utf-8")
        elif path == "/api/state":
            body = json.dumps(bus.snapshot()).encode()
            self._send(HTTPStatus.OK, "application/json", body)
        elif path == "/events":
            self._stream_events()
        else:
            self._send(HTTPStatus.NOT_FOUND, "text/plain", b"not found")

    def _send(self, status: HTTPStatus, ctype: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, ctype: str) -> None:
        try:
            self._send(HTTPStatus.OK, ctype, path.read_bytes())
        except FileNotFoundError:
            self._send(HTTPStatus.NOT_FOUND, "text/plain", b"missing static file")

    def _stream_events(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = bus.subscribe()
        try:
            self._write_sse("snapshot", bus.snapshot())
            while True:
                try:
                    event = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                self._write_sse("event", event)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            bus.unsubscribe(q)

    def _write_sse(self, name: str, data: Any) -> None:
        payload = json.dumps(data)
        self.wfile.write(f"event: {name}\ndata: {payload}\n\n".encode())
        self.wfile.flush()


_server: ThreadingHTTPServer | None = None


def start(port: int = 8765, host: str = "127.0.0.1") -> str:
    """Start the dashboard in a daemon thread and return its URL."""
    global _server
    if _server is not None:
        return f"http://{host}:{_server.server_address[1]}/"
    _server = ThreadingHTTPServer((host, port), _Handler)
    _server.daemon_threads = True
    threading.Thread(target=_server.serve_forever, name="saul-dashboard", daemon=True).start()
    url = f"http://{host}:{_server.server_address[1]}/"
    logger.info("operator dashboard at %s", url)
    return url


def stop() -> None:
    global _server
    if _server is not None:
        _server.shutdown()
        _server = None
