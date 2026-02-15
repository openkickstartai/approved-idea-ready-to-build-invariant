"""Pytest plugin for Invariant Miner — run with `pytest --invariants`."""
import pytest
import invariant_miner as inv


def pytest_addoption(parser):
    """Register the --invariants CLI flag."""
    parser.addoption(
        "--invariants", action="store_true", default=False,
        help="Print discovered invariants after test session",
    )


@pytest.fixture
def trace():
    """Fixture that provides the @trace decorator and clears state."""
    inv.clear()
    yield inv.trace


def pytest_terminal_summary(terminalreporter, config):
    """Display mined invariants at the end of the test run."""
    if not config.getoption("--invariants", default=False):
        return
    invariants = inv.mine()
    if not invariants:
        return
    terminalreporter.write_sep("=", "Discovered Invariants")
    for name, invs in invariants.items():
        terminalreporter.write_line(f"\n  {name}:")
        for kind, val in invs:
            terminalreporter.write_line(f"    - {kind}: {val}")
    code = inv.generate_assertions()
    if code:
        terminalreporter.write_line("")
        terminalreporter.write_sep("-", "Generated Assertions (copy into your code)")
        for line in code.split("\n"):
            terminalreporter.write_line(f"  {line}")
    terminalreporter.write_line("")
