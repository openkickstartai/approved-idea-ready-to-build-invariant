"""Tests for invariant_miner core engine."""
import invariant_miner as inv


def setup_function():
    inv.clear()


def test_numeric_invariants_sign_and_type():
    """abs() should yield non_negative sign and consistent int type."""
    @inv.trace
    def absolute(x):
        return abs(x)

    for v in [-5, -1, 0, 3, 7, 100]:
        absolute(v)

    result = inv.mine("absolute")
    assert "absolute" in result
    kinds = [k for k, _ in result["absolute"]]
    assert "type" in kinds
    assert "sign" in kinds
    assert "not_none" in kinds
    sign_val = next(v for k, v in result["absolute"] if k == "sign")
    assert sign_val == "non_negative"
    type_val = next(v for k, v in result["absolute"] if k == "type")
    assert type_val == "int"


def test_sorted_and_length_preserved():
    """sorted() should yield sorted=True and len_preserved."""
    @inv.trace
    def sort_list(items):
        return sorted(items)

    sort_list([3, 1, 2])
    sort_list([5, 4])
    sort_list([1])

    result = inv.mine("sort_list")
    kinds = [k for k, _ in result["sort_list"]]
    assert "sorted" in kinds
    assert "len_preserved" in kinds


def test_assertion_generation_for_double():
    """double(x) should generate positive, gte_arg assertions."""
    @inv.trace
    def double(x):
        return x * 2

    for v in [1, 2, 3, 5, 10]:
        double(v)

    code = inv.generate_assertions("double")
    assert "isinstance(result, int)" in code
    assert "result > 0" in code
    assert "result >= args[0]" in code


def test_string_lowercase_invariant():
    """normalize() should detect lowercase invariant."""
    @inv.trace
    def normalize(s):
        return s.lower().strip()

    normalize("Hello")
    normalize("WORLD")
    normalize(" Foo ")

    result = inv.mine("normalize")
    kinds = [k for k, _ in result["normalize"]]
    assert "lowercase" in kinds
    assert "type" in kinds
    type_val = next(v for k, v in result["normalize"] if k == "type")
    assert type_val == "str"


def test_clear_traces_resets_state():
    """clear() should remove all collected trace data."""
    @inv.trace
    def add(a, b):
        return a + b

    add(1, 2)
    add(3, 4)
    assert inv.mine()  # has data
    inv.clear()
    assert not inv.mine()  # empty after clear


def test_insufficient_traces_skipped():
    """Functions with < 2 traces should not produce invariants."""
    @inv.trace
    def once(x):
        return x + 1

    once(5)
    result = inv.mine("once")
    assert "once" not in result  # need at least 2 observations
