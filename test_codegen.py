"""Tests for codegen \u2014 assertion code generation from mined invariants.

Every test verifies:
1. The generated string contains the expected assertion expression.
2. ``compile()`` confirms syntactic validity.
3. ``exec()`` on mock data confirms semantic correctness.
"""
import pytest
import codegen


# ------------------------------------------------------------------ #
#  Standard-style assertions                                          #
# ------------------------------------------------------------------ #

def test_type_invariant_standard():
    """type invariant \u2192 isinstance check with message."""
    invs = [("type", "int")]
    code = codegen.generate_asserts(invs)
    assert "assert isinstance(result, int)" in code
    assert "Invariant:" in code
    compile(code, "<test_type>", "exec")
    exec(code, {"result": 42})


def test_sign_positive():
    """positive sign \u2192 result > 0."""
    invs = [("sign", "positive")]
    code = codegen.generate_asserts(invs)
    assert "result > 0" in code
    compile(code, "<test_sign_pos>", "exec")
    exec(code, {"result": 7})


def test_sign_non_negative():
    """non_negative sign \u2192 result >= 0 (zero must pass)."""
    invs = [("sign", "non_negative")]
    code = codegen.generate_asserts(invs)
    assert "result >= 0" in code
    compile(code, "<test_sign_nn>", "exec")
    exec(code, {"result": 0})


def test_sign_negative():
    """negative sign \u2192 result < 0."""
    invs = [("sign", "negative")]
    code = codegen.generate_asserts(invs)
    assert "result < 0" in code
    compile(code, "<test_sign_neg>", "exec")
    exec(code, {"result": -3})


def test_not_none():
    """not_none \u2192 result is not None."""
    invs = [("not_none", True)]
    code = codegen.generate_asserts(invs)
    assert "result is not None" in code
    compile(code, "<test_nn>", "exec")
    exec(code, {"result": "anything"})


def test_sorted_invariant():
    """sorted \u2192 result == sorted(result)."""
    invs = [("sorted", True)]
    code = codegen.generate_asserts(invs)
    assert "sorted(result)" in code
    compile(code, "<test_sorted>", "exec")
    exec(code, {"result": [1, 2, 3]})


def test_range_invariant():
    """range \u2192 lo <= result <= hi."""
    invs = [("range", (0, 100))]
    code = codegen.generate_asserts(invs)
    assert "0 <= result <= 100" in code
    compile(code, "<test_range>", "exec")
    exec(code, {"result": 50})


def test_fixed_length():
    """fixed_length \u2192 len(result) == N."""
    invs = [("fixed_length", 3)]
    code = codegen.generate_asserts(invs)
    assert "len(result) == 3" in code
    compile(code, "<test_fixlen>", "exec")
    exec(code, {"result": [1, 2, 3]})


# ------------------------------------------------------------------ #
#  Relational / variable-name assertions                              #
# ------------------------------------------------------------------ #

def test_len_preserved_with_var_names():
    """len_preserved + var_names \u2192 len(output) == len(items)."""
    invs = [("len_preserved", True)]
    code = codegen.generate_asserts(
        invs, var_names={"result": "output", "args[0]": "items"},
    )
    assert "len(output) == len(items)" in code
    compile(code, "<test_lp>", "exec")
    exec(code, {"output": [1, 2, 3], "items": [4, 5, 6]})


def test_gte_arg_relational():
    """gte_arg with var_names \u2192 result >= x."""
    invs = [("gte_arg", 0)]
    code = codegen.generate_asserts(
        invs, var_names={"result": "result", "args[0]": "x"},
    )
    assert "result >= x" in code
    compile(code, "<test_gte>", "exec")
    exec(code, {"result": 10, "x": 5})


def test_gte_arg_default_var():
    """gte_arg without var_names \u2192 result >= args[0]."""
    invs = [("gte_arg", 0)]
    code = codegen.generate_asserts(invs)
    assert "result >= args[0]" in code
    compile(code, "<test_gte_def>", "exec")
    args = [5]
    exec(code, {"result": 10, "args": args})


def test_lowercase_invariant():
    """lowercase \u2192 result == result.lower()."""
    invs = [("lowercase", True)]
    code = codegen.generate_asserts(invs)
    assert "result.lower()" in code
    compile(code, "<test_lower>", "exec")
    exec(code, {"result": "hello"})


# ------------------------------------------------------------------ #
#  Pytest style                                                       #
# ------------------------------------------------------------------ #

def test_pytest_style_no_message():
    """pytest style \u2192 bare assert, no message string."""
    invs = [("type", "int"), ("sign", "positive"), ("not_none", True)]
    code = codegen.generate_asserts(invs, style="pytest")
    assert "Invariant" not in code
    lines = [l for l in code.strip().split("\n") if l.strip()]
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("assert ")
        # No trailing message: the line should NOT contain ", '"
        assert ", '" not in line
    compile(code, "<test_pytest>", "exec")
    exec(code, {"result": 42})


# ------------------------------------------------------------------ #
#  Confidence annotation                                              #
# ------------------------------------------------------------------ #

def test_confidence_in_message():
    """confidence_map values appear in assertion message."""
    invs = [("type", "float")]
    code = codegen.generate_asserts(invs, confidence_map={"type": 0.98})
    assert "confidence=0.98" in code
    compile(code, "<test_conf>", "exec")
    exec(code, {"result": 3.14})


def test_confidence_tuple_key():
    """confidence_map keyed by (kind, value) tuple."""
    invs = [("sign", "positive")]
    code = codegen.generate_asserts(
        invs, confidence_map={("sign", "positive"): 0.95},
    )
    assert "confidence=0.95" in code
    compile(code, "<test_conf_tup>", "exec")
    exec(code, {"result": 1})


# ------------------------------------------------------------------ #
#  Decorator mode                                                     #
# ------------------------------------------------------------------ #

def test_decorator_mode_structure():
    """Decorator output contains import, def, functools.wraps."""
    invs = [("type", "int"), ("sign", "positive")]
    code = codegen.generate_asserts(invs, style="decorator", func_name="double")
    assert "import functools" in code
    assert "def invariant_check(func):" in code
    assert "@functools.wraps(func)" in code
    assert "isinstance(result, int)" in code
    assert "result > 0" in code
    assert "double" in code
    compile(code, "<test_dec_struct>", "exec")


def test_decorator_mode_exec():
    """Generated decorator actually works at runtime."""
    invs = [("type", "int"), ("sign", "positive")]
    code = codegen.generate_asserts(invs, style="decorator", func_name="double")
    ns = {}
    exec(code, ns)

    @ns["invariant_check"]
    def double(x):
        return x * 2

    assert double(5) == 10
    assert double(1) == 2


def test_decorator_catches_violation():
    """Decorator raises AssertionError when invariant is violated."""
    invs = [("sign", "positive")]
    code = codegen.generate_asserts(invs, style="decorator", func_name="bad")
    ns = {}
    exec(code, ns)

    @ns["invariant_check"]
    def bad(x):
        return -1

    with pytest.raises(AssertionError, match="Invariant"):
        bad(5)


# ------------------------------------------------------------------ #
#  Edge cases                                                         #
# ------------------------------------------------------------------ #

def test_multiple_invariants_combined():
    """Multiple invariants \u2192 one assert per invariant."""
    invs = [
        ("type", "int"),
        ("sign", "positive"),
        ("not_none", True),
        ("range", (1, 100)),
    ]
    code = codegen.generate_asserts(invs)
    lines = [l for l in code.strip().split("\n") if l.strip()]
    assert len(lines) == 4
    compile(code, "<test_multi>", "exec")
    exec(code, {"result": 50})


def test_unknown_invariant_skipped():
    """Unknown invariant kinds are silently skipped."""
    invs = [("unknown_thing", 42), ("type", "int")]
    code = codegen.generate_asserts(invs)
    lines = [l for l in code.strip().split("\n") if l.strip()]
    assert len(lines) == 1
    assert "isinstance(result, int)" in code


def test_empty_invariants():
    """Empty invariant list \u2192 empty string."""
    code = codegen.generate_asserts([])
    assert code == ""


def test_exec_fails_on_violation():
    """Standard assertion actually fails on bad data."""
    invs = [("sign", "positive")]
    code = codegen.generate_asserts(invs)
    with pytest.raises(AssertionError):
        exec(code, {"result": -5})
