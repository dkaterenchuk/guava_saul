import json
import urllib.request

from saul import dashboard
from saul.dashboard import Bus, mask_number


def test_mask_number():
    assert mask_number("+14842951424") == "•••-1424"
    assert mask_number(None) == "unknown number"
    assert mask_number("12") == "unknown number"


def test_bus_builds_turn_by_turn_state():
    b = Bus()
    b.emit("c1", "call_start", label="phone •••-1424")
    b.emit("c1", "phase", phase="intake")
    b.emit("c1", "agent", text="Which state are you in?")
    b.emit("c1", "caller", id="c-u1", text="Cali")
    b.emit("c1", "caller", id="c-u1", text="California.")  # refined transcript, same turn
    b.emit("c1", "agent", text="Got it.", interrupted=True)
    b.emit("c1", "safety", category="domestic_violence")
    b.emit("c1", "case", case={"state": "California"})
    b.emit("c1", "advice", advice={"top3": ["a", "b", "c"]}, provider="fallback")
    b.emit("c1", "call_end", reason="user-hangup")

    snap = b.snapshot()
    assert len(snap["calls"]) == 1
    c = snap["calls"][0]
    assert c["phase"] == "intake"
    roles = [t["role"] for t in c["turns"]]
    assert roles == ["agent", "caller", "agent"]
    assert c["turns"][1]["text"] == "California."
    assert c["turns"][2]["interrupted"] is True
    assert c["safety"] == ["domestic_violence"]
    assert c["case"]["state"] == "California"
    assert c["advice_provider"] == "fallback"
    assert c["termination_reason"] == "user-hangup"
    assert c["ended_at"] is not None


def test_unknown_call_is_created_on_first_event():
    b = Bus()
    b.emit("x", "agent", text="hi")
    assert b.snapshot()["calls"][0]["turns"][0]["text"] == "hi"


def test_subscribers_receive_events():
    b = Bus()
    q = b.subscribe()
    b.emit("c1", "call_start", label="browser")
    assert q.get(timeout=1)["type"] == "call_start"
    b.unsubscribe(q)


def test_http_server_serves_page_and_state():
    url = dashboard.start(port=0)  # ephemeral port
    try:
        dashboard.bus.reset()
        dashboard.bus.emit("c9", "call_start", label="browser")
        html = urllib.request.urlopen(url, timeout=3).read().decode()
        assert "operator console" in html and "EventSource" in html
        state = json.loads(urllib.request.urlopen(url + "api/state", timeout=3).read())
        assert state["calls"][0]["id"] == "c9"
    finally:
        dashboard.stop()
