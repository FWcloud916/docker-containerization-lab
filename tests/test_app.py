from app.main import livez


def test_liveness_does_not_require_database():
    assert livez() == {"status": "live"}
