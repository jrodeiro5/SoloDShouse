from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session


def test_collector_unavailable_error():
    err = CollectorUnavailableError("source down")
    assert str(err) == "source down"


def test_step_error():
    orig = ValueError("something wrong")
    err = StepError(step_number=1, step_name="test_step", original=orig)
    assert err.step_number == 1
    assert err.step_name == "test_step"
    assert err.original is orig
    assert "Step 1 (test_step) failed: something wrong" in str(err)


def test_make_session():
    session = make_session()
    assert session is not None
    assert "https://" in session.adapters
    assert "http://" in session.adapters
