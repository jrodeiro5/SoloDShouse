from __future__ import annotations

from ingestion.exceptions import CollectorUnavailableError, StepError


def test_collector_unavailable_error():
    err = CollectorUnavailableError("Source down")
    assert str(err) == "Source down"


def test_step_error():
    orig = ValueError("bad data")
    err = StepError(step_number=1, step_name="fetch", original=orig)
    assert err.step_number == 1
    assert err.step_name == "fetch"
    assert err.original is orig
    assert "Step 1 (fetch) failed: bad data" in str(err)
