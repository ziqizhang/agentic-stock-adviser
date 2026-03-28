"""Smoke test — verifies the package is importable and test infrastructure works."""


def test_import():
    import stock_adviser

    assert stock_adviser.__doc__ is not None
