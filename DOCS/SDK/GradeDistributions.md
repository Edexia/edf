# GradeDistributions Class

> **Navigation**: [SDK](README.md) | [EDF](EDF.md) | [Submission](Submission.md)

Container for the three probability distributions representing different marker noise levels.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `optimistic` | `list[float]` | Low-noise scenario (tight) |
| `expected` | `list[float]` | Medium-noise scenario (baseline) |
| `pessimistic` | `list[float]` | High-noise scenario (wide) |

## Distribution Requirements

Each distribution:
- Has length `max_grade + 1`
- Contains non-negative values
- Sums to 1.0 (within 0.0001 tolerance)

## Understanding the Three Modes

The modes model **noise levels in human marker behavior**, not systematic biases:

| Mode | Noise Level | Distribution Shape | Use Case |
|------|-------------|-------------------|----------|
| optimistic | Low | Tight (small variance) | Markers grade consistently |
| expected | Medium | Baseline | Typical marker variability |
| pessimistic | High | Wide (large variance) | Markers are inconsistent |

**Important**: These do NOT represent "harsh" vs "lenient" graders. They model randomness/variance, not bias.

## Generating Distributions

Avoid naive fixed standard deviations. Real marker noise varies based on rubric clarity, question ambiguity, and submission quality.

### Simple Helper (for prototyping)

```python
import math

def generate_distribution(peak: int, max_grade: int, spread: float) -> list[float]:
    """
    Generate bell-curve distribution centered on peak.

    spread: Distribution width as fraction of max_grade.
            Lower = tighter (low noise), higher = wider (high noise).
    """
    dist = []
    for i in range(max_grade + 1):
        diff = abs(i - peak)
        prob = math.exp(-(diff ** 2) / (2 * (spread * max_grade) ** 2))
        dist.append(prob)
    total = sum(dist)
    return [p / total for p in dist]

# Example for grade 15/20
optimistic = generate_distribution(15, 20, spread=0.10)   # Low noise
expected = generate_distribution(15, 20, spread=0.15)     # Medium noise
pessimistic = generate_distribution(15, 20, spread=0.20)  # High noise
```

### Production Considerations

For production use, consider:
- Deriving spread from actual marker behavior data
- Modeling rubric clarity effects
- Accounting for question-specific ambiguity
- Using historical grading variance data

## Accessing Distributions

```python
with EDF.open("file.edf") as edf:
    sub = edf.get_submission("alice")

    print(f"Optimistic: {sub.distributions.optimistic}")
    print(f"Expected: {sub.distributions.expected}")
    print(f"Pessimistic: {sub.distributions.pessimistic}")
```
