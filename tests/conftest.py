import pytest

from mustra import corrections


@pytest.fixture(autouse=True)
def original_theory():
    """Every test starts and ends with the shipped theory (no user corrections)."""
    corrections.apply({})
    yield
    corrections.apply({})
