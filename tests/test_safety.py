from saul import safety


def test_no_signal_on_ordinary_story():
    assert safety.scan("I got pulled over last Friday and blew just over the limit.") is None
    assert safety.scan("Store security stopped me in the parking lot and took my name.") is None


def test_domestic_violence_signal():
    s = safety.scan("my partner will hurt me if I don't leave before he's back")
    assert s is not None and s.category == "domestic_violence"


def test_self_harm_signal():
    s = safety.scan("honestly I just want to kill myself over this")
    assert s is not None and s.category == "self_harm"


def test_active_arrest_signal():
    s = safety.scan("the cops are here right now and they're arresting me")
    assert s is not None and s.category in {"active_arrest", "emergency"}


def test_emergency_signal():
    s = safety.scan("he's outside right now and he has a knife")
    assert s is not None and s.category == "emergency"


def test_scripts_exist_for_every_category():
    for cat in ["emergency", "self_harm", "domestic_violence", "child", "active_arrest"]:
        text = safety.safety_script(safety.SafetySignal(cat, "x"))
        assert "911" in text or "988" in text or "lawyer" in text


def test_wants_human_and_done():
    for phrase in [
        "can I just talk to a real lawyer?", "I want a lawyer", "can I speak with someone",
        "is this a real person", "put me through to somebody", "get me an attorney",
    ]:
        assert safety.wants_human(phrase), phrase
    assert not safety.wants_human("are you a bot")
    assert not safety.wants_human("the lawyer at the store said nothing")
    assert safety.is_done("thanks, that's everything")
    assert not safety.is_done("I have one more question")
