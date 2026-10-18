from saul.case_file import REQUIRED_KEYS, CaseFile, intake_fields


def test_intake_fields_cover_required_keys_in_order():
    assert [f.key for f in intake_fields()] == REQUIRED_KEYS
    assert all(f.required for f in intake_fields())


def test_complete_and_missing():
    c = CaseFile()
    assert not c.is_complete() and c.missing() == REQUIRED_KEYS
    for k in REQUIRED_KEYS:
        setattr(c, k, "x")
    assert c.is_complete()


def test_has_deadline():
    assert not CaseFile(charges_or_court_dates="none yet").has_deadline()
    assert CaseFile(charges_or_court_dates="court Nov 3").has_deadline()


def test_summary_reads_back_every_slot():
    c = CaseFile(
        state="Texas", what_happened="accused of not scanning an item", when_where="yesterday, big-box store",
        parties_involved="store security", police_contact="none", charges_or_court_dates="none yet",
        statements_already_made="refused to sign", evidence_witnesses="receipt", caller_goal="protect my license",
    )
    s = c.summary_text()
    for piece in ["Texas", "not scanning", "store security", "haven't been involved", "receipt", "protect my license"]:
        assert piece in s


def test_from_dict_ignores_unknown_and_round_trips():
    c = CaseFile(state="Ohio", corrections=["it was Tuesday"])
    d = c.to_dict() | {"junk": 1}
    assert CaseFile.from_dict(d) == c
