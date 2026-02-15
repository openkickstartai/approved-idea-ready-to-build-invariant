"""Invariant Miner — discover code invariants from test run traces."""
import functools
from collections import defaultdict

_traces = defaultdict(list)


def trace(func):
    """Decorator that records every call's args and result."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        _traces[func.__name__].append({"args": args, "kw": kwargs, "result": result})
        return result
    return wrapper


def clear():
    """Reset all collected traces."""
    _traces.clear()


def mine(func_name=None):
    """Analyze traces and return discovered invariants per function."""
    targets = {func_name: _traces[func_name]} if func_name else dict(_traces)
    return {n: _detect(recs) for n, recs in targets.items() if len(recs) >= 2}


def _detect(records):
    invs = []
    ress = [r["result"] for r in records]
    # Type consistency
    types = set(type(v).__name__ for v in ress)
    if len(types) == 1:
        invs.append(("type", types.pop()))
    # Numeric properties
    if all(isinstance(v, (int, float)) for v in ress):
        mn, mx = min(ress), max(ress)
        if mn > 0:
            invs.append(("sign", "positive"))
        elif mn >= 0:
            invs.append(("sign", "non_negative"))
        elif mx < 0:
            invs.append(("sign", "negative"))
        invs.append(("range", (mn, mx)))
    # None check
    if all(v is not None for v in ress):
        invs.append(("not_none", True))
    # List properties
    if all(isinstance(v, list) for v in ress):
        if all(v == sorted(v) for v in ress if v):
            invs.append(("sorted", True))
        lens = [len(v) for v in ress]
        if len(set(lens)) == 1:
            invs.append(("fixed_length", lens[0]))
    # String properties
    if all(isinstance(v, str) for v in ress):
        if all(v == v.lower() for v in ress):
            invs.append(("lowercase", True))
        if all(v == v.upper() for v in ress):
            invs.append(("uppercase", True))
    # Arg-result relationships
    ac = [len(r["args"]) for r in records]
    if ac and all(c == ac[0] for c in ac) and ac[0] > 0:
        for i in range(ac[0]):
            ai = [r["args"][i] for r in records]
            if all(isinstance(a, (int, float)) and isinstance(v, (int, float))
                   for a, v in zip(ai, ress)):
                if all(v >= a for a, v in zip(ai, ress)):
                    invs.append(("result_gte_arg", i))
                if all(v <= a for a, v in zip(ai, ress)):
                    invs.append(("result_lte_arg", i))
            if all(hasattr(a, '__len__') and hasattr(v, '__len__')
                   for a, v in zip(ai, ress)):
                if all(len(v) == len(a) for a, v in zip(ai, ress)):
                    invs.append(("len_preserved", i))
    return invs


_TPL = {
    "type": "assert isinstance(result, {val})",
    "sign": {"positive": "assert result > 0", "non_negative": "assert result >= 0",
             "negative": "assert result < 0"},
    "range": "assert {val[0]} <= result <= {val[1]}  # observed range",
    "not_none": "assert result is not None",
    "sorted": "assert result == sorted(result)",
    "fixed_length": "assert len(result) == {val}",
    "lowercase": "assert result == result.lower()",
    "uppercase": "assert result == result.upper()",
    "result_gte_arg": "assert result >= args[{val}]",
    "result_lte_arg": "assert result <= args[{val}]",
    "len_preserved": "assert len(result) == len(args[{val}])",
}


def generate_assertions(func_name=None):
    """Generate assertion source code from discovered invariants."""
    lines = []
    for name, invs in mine(func_name).items():
        lines.append(f"# Discovered invariants for `{name}`:")
        for kind, val in invs:
            tmpl = _TPL.get(kind, "")
            if isinstance(tmpl, dict):
                lines.append(tmpl.get(val, f"# {kind}: {val}"))
            else:
                lines.append(tmpl.format(val=val))
    return "\n".join(lines)
