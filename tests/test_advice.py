from saul.advice import Advice, AdviceItem, advice_chunks, advice_notes, check_advice, fallback_advice, find_why
from saul.case_file import CaseFile


def _case(deadline="none yet"):
    return CaseFile(
        state="California", what_happened="pulled over, breathalyzer over the limit", when_where="Friday night, Pasadena",
        parties_involved="one officer", police_contact="cited", charges_or_court_dates=deadline,
        statements_already_made="told my roommate", evidence_witnesses="the ticket", caller_goal="keep my license",
    )


def test_fallback_advice_is_valid_and_bounded():
    adv = fallback_advice(_case())
    assert 1 <= len(adv.do) <= 3 and 1 <= len(adv.dont) <= 3 and 2 <= len(adv.options) <= 3
    assert len(adv.top3) == 3
    assert any("lawyer" in o.name.lower() for o in adv.options)


def test_fallback_puts_deadline_first():
    adv = fallback_advice(_case("court date November 3rd"))
    assert "November 3rd" in adv.do[0].action


def test_chunks_are_short_and_nonempty():
    adv = fallback_advice(_case())
    chunks = advice_chunks(adv)
    assert len(chunks) == 2 + len(adv.options)
    for c in chunks:
        assert c and c.endswith(".") and len(c) < 600


def test_schema_forbids_extra_keys():
    schema = Advice.model_json_schema()
    assert schema["additionalProperties"] is False


def test_find_why_matches_relevant_item():
    adv = fallback_advice(_case())
    why = find_why(adv, "why can't I post about it online?")
    assert why and "screenshot" in why.lower()
    assert find_why(adv, "zzz qqq") is None


def test_notes_carry_rules():
    notes = advice_notes(fallback_advice(_case()))
    assert any("predict" in r for r in notes["rules"])


def test_policy_guard_catches_predictions_and_statutes():
    adv = fallback_advice(_case())
    assert check_advice(adv) == []
    adv.do[0] = AdviceItem(action="Relax, you'll win this.", why="Strong case.")
    adv.top3[0] = "See Penal Code 647."
    hits = check_advice(adv)
    assert len(hits) == 3


def test_fallback_has_no_guarantee_language():
    adv = fallback_advice(_case())
    text = " ".join(s.lower() for o in adv.options for s in [o.name, o.saul_take, *o.pros, *o.cons])
    assert "nothing you say gets used" not in text and "only gets worse" not in text
