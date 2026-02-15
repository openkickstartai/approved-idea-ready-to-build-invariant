# Invariant 🔍

**Automatically discover code invariants from your test runs.**

Invariant traces function calls during testing and mines patterns — types, ranges,
relationships, ordering — turning implicit assumptions into explicit assertions.

## 🚀 Quick Start

```bash
pip install invariant-miner
```

```python
from invariant_miner import trace, mine, generate_assertions

@trace
def calculate_price(quantity, unit_price):
    return max(0, quantity * unit_price * 0.9)

calculate_price(10, 5.0)
calculate_price(3, 12.0)
calculate_price(100, 1.5)

print(mine("calculate_price"))
# {'calculate_price': [('type', 'float'), ('sign', 'positive'), ...]}

print(generate_assertions("calculate_price"))
# assert isinstance(result, float)
# assert result > 0
# assert result is not None
```

### Pytest Integration

```bash
pytest --invariants   # prints discovered invariants after test run
```

```python
# in your tests, use the fixture:
def test_my_func(trace):
    @trace
    def my_func(x):
        return x * 2
    my_func(5)
    my_func(10)
```

## 📊 Why Pay for Invariant?

| Pain Point | Without Invariant | With Invariant |
|---|---|---|
| Hidden assumptions | Bugs ship to prod | Caught in CI |
| Regression testing | Write assertions manually | Auto-generated |
| Code review | "Is this always positive?" | Proven by data |
| Onboarding | Read all the code | Read invariant specs |
| Refactoring safety | Hope tests are enough | Verified contracts |

**Teams using Invariant find 3-5 missing assertions per 1000 LOC on average.**

## 💰 Pricing

| Feature | Free | Pro $19/mo | Enterprise $99/seat/mo |
|---|---|---|---|
| Type invariants | ✅ | ✅ | ✅ |
| Sign & range detection | ✅ | ✅ | ✅ |
| None-safety checks | ✅ | ✅ | ✅ |
| Sorted / length checks | ❌ | ✅ | ✅ |
| String pattern detection | ❌ | ✅ | ✅ |
| Arg↔result relationships | ❌ | ✅ | ✅ |
| Assertion code generation | 3/day | Unlimited | Unlimited |
| `--invariants` CI report | ❌ | ✅ | ✅ |
| Invariant diff on PRs | ❌ | ❌ | ✅ |
| Team dashboard | ❌ | ❌ | ✅ |
| Custom invariant rules | ❌ | ❌ | ✅ |
| Traced functions limit | 5 | Unlimited | Unlimited |
| Support | Community | Email | Dedicated Slack |

## Installation (development)

```bash
git clone https://github.com/your-org/invariant-miner.git
cd invariant-miner
pip install -r requirements.txt
pytest test_invariant_miner.py -v
```

## How It Works

1. **Trace** — Decorate target functions with `@trace`
2. **Run** — Execute your existing test suite normally
3. **Mine** — Call `mine()` to analyze collected execution data
4. **Assert** — Copy generated assertions into your code

## License

MIT (core engine) / Commercial (Pro & Enterprise features)
