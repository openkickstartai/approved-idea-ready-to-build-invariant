"""codegen.py \u2014 Generate assertion code from mined invariants.

Core paid feature: convert discovered invariants into insertable assert
statements.  Supports three output styles:

* **standard** \u2014 ``assert expr, 'Invariant: description (confidence=X)'``
* **pytest**   \u2014 bare ``assert expr`` (relies on pytest assertion rewriting)
* **decorator** \u2014 a standalone ``@invariant_check`` wrapper function
"""


def _resolve_var(key, var_names):
    """Return the user-supplied variable name or fall back to *key*."""
    if var_names and key in var_names:
        return var_names[key]
    return key


def _conf_suffix(kind, value, confidence_map):
    """Build a confidence annotation like `` (confidence=0.98)``."""
    if not confidence_map:
        return ""
    conf = confidence_map.get(kind)
    if conf is None:
        conf = confidence_map.get((kind, value))
    if conf is not None:
        return f" (confidence={conf:.2f})"
    return ""


_TYPE_MAP = {
    "int": "int", "float": "float", "str": "str",
    "bool": "bool", "list": "list", "dict": "dict",
    "tuple": "tuple", "set": "set", "NoneType": "type(None)",
}

_SIGN_OPS = {
    "positive": "> 0",
    "non_negative": ">= 0",
    "negative": "< 0",
}


def _inv_to_expr(kind, value, var_names=None):
    """Convert a single invariant tuple to ``(expression, description)``.

    Returns *None* for unrecognised invariant kinds so callers can skip them.
    """
    rv = _resolve_var("result", var_names)

    if kind == "type":
        t = _TYPE_MAP.get(value, value)
        return f"isinstance({rv}, {t})", f"{rv} should be {value}"

    if kind == "sign":
        op = _SIGN_OPS.get(value)
        if op:
            label = value.replace("_", "-")
            return f"{rv} {op}", f"{rv} should be {label}"

    if kind == "range":
        lo, hi = value
        return f"{lo} <= {rv} <= {hi}", f"{rv} in range [{lo}, {hi}]"

    if kind == "not_none":
        return f"{rv} is not None", f"{rv} should not be None"

    if kind == "sorted":
        return f"{rv} == sorted({rv})", f"{rv} should be sorted"

    if kind == "fixed_length":
        return f"len({rv}) == {value}", f"len({rv}) should be {value}"

    if kind == "len_preserved":
        av = _resolve_var("args[0]", var_names)
        return f"len({rv}) == len({av})", f"len({rv}) should equal len({av})"

    if kind == "lowercase":
        return f"{rv} == {rv}.lower()", f"{rv} should be lowercase"

    if kind == "uppercase":
        return f"{rv} == {rv}.upper()", f"{rv} should be uppercase"

    if kind == "gte_arg":
        idx = value if isinstance(value, int) else 0
        av = _resolve_var(f"args[{idx}]", var_names)
        return f"{rv} >= {av}", f"{rv} should be >= {av}"

    if kind == "lte_arg":
        idx = value if isinstance(value, int) else 0
        av = _resolve_var(f"args[{idx}]", var_names)
        return f"{rv} <= {av}", f"{rv} should be <= {av}"

    return None


def generate_asserts(invariants, style="standard", func_name=None,
                     confidence_map=None, var_names=None):
    """Generate assertion source code from invariant tuples.

    Parameters
    ----------
    invariants : list[tuple[str, Any]]
        ``(kind, value)`` pairs produced by :func:`invariant_miner.mine`.
    style : str
        ``"standard"`` | ``"pytest"`` | ``"decorator"``.
    func_name : str | None
        Optional function name used in decorator comments.
    confidence_map : dict | None
        ``kind`` or ``(kind, value)`` \u2192 ``float`` confidence score.
    var_names : dict | None
        Map generic names (``"result"``, ``"args[0]"``) to real identifiers.

    Returns
    -------
    str
        Syntactically valid Python source.
    """
    if style == "decorator":
        return _gen_decorator(invariants, func_name, confidence_map, var_names)

    lines = []
    for kind, value in invariants:
        pair = _inv_to_expr(kind, value, var_names)
        if pair is None:
            continue
        expr, desc = pair
        if style == "pytest":
            lines.append(f"assert {expr}")
        else:
            cs = _conf_suffix(kind, value, confidence_map)
            lines.append(f"assert {expr}, 'Invariant: {desc}{cs}'")
    return "\n".join(lines)


def _gen_decorator(invariants, func_name=None, confidence_map=None,
                   var_names=None):
    """Emit a self-contained ``@invariant_check`` decorator."""
    # Inside the wrapper, result and args are always local names.
    inner = dict(var_names) if var_names else {}
    inner["result"] = "result"
    # args[N] stays as-is \u2014 wrapper receives *args.

    body = []
    for kind, value in invariants:
        pair = _inv_to_expr(kind, value, inner)
        if pair is None:
            continue
        expr, desc = pair
        cs = _conf_suffix(kind, value, confidence_map)
        body.append(f"        assert {expr}, 'Invariant: {desc}{cs}'")

    if not body:
        body.append("        pass")

    checks = "\n".join(body)
    comment = f"  # Invariant checks for {func_name}" if func_name else ""

    return (
        "import functools\n"
        "\n"
        "\n"
        f"def invariant_check(func):{comment}\n"
        "    @functools.wraps(func)\n"
        "    def wrapper(*args, **kwargs):\n"
        "        result = func(*args, **kwargs)\n"
        f"{checks}\n"
        "        return result\n"
        "    return wrapper"
    )
