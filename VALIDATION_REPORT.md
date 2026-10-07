# Validation Report

This report records verification performed on the repository state audited on 2026-10-07.

## Project Guide Audit Status

The implementation was compared against the Project Guide requirements for:

- repository structure and reproducibility;
- three-factor trust gate;
- Bayesian evidence and context separation;
- six remediation actions;
- simulator and outcome model;
- benchmark baselines and four metrics;
- deterministic execution;
- threshold sensitivity;
- paper structure, results, limitations, and references;
- decision logging and documentation.

## Verified Commands

### Test suite

```text
python -m pytest -q
```

Result:

```text
11 passed
```

### Deterministic benchmark

```text
python benchmark.py --seed 42 --incidents 1000
```

The command was executed twice. The two seed-42 JSON result files were byte-identical.

### Second benchmark seed

```text
python benchmark.py --seed 43 --incidents 1000
```

Executed successfully.

### Evidence accumulation

```text
python run_learning_experiment.py
```

Executed successfully.

Observed results:

- `restart_service`: 3 ESCALATE, 23 PROPOSE, 74 AUTO; first AUTO at incident 10.
- `drain_node`: 100 ESCALATE, 0 PROPOSE, 0 AUTO.

### Threshold sweeps

```text
python threshold_sweep.py --seed 42 --incidents 1000
python threshold_sweep.py --seed 43 --incidents 1000
```

Both executed successfully. Each sweep evaluated 69 valid threshold combinations.

### Paper compilation

The LaTeX paper was compiled twice with `pdflatex`.

Result:

- compilation successful;
- 8-page PDF generated;
- no undefined-reference or compilation warning remained after the second pass.

## Benchmark Results

### Seed 42

| Metric | Always Ask | Always Act | EarnedAutonomy |
|---|---:|---:|---:|
| Automatic resolution rate | 0.000 | 0.528 | 0.000 |
| Mean time to recovery | 291.685 s | 171.685 s | 443.905 s |
| Human interruptions | 1000 | 472 | 1000 |
| Unsafe automatic executions | 0 | 472 | 2 |

### Seed 43

| Metric | Always Ask | Always Act | EarnedAutonomy |
|---|---:|---:|---:|
| Automatic resolution rate | 0.000 | 0.538 | 0.011 |
| Mean time to recovery | 288.300 s | 168.300 s | 442.320 s |
| Human interruptions | 1000 | 462 | 989 |
| Unsafe automatic executions | 0 | 462 | 0 |

## Threshold Sensitivity

At PROPOSE threshold 0.35 for seed 42:

| AUTO threshold | Automation | Unsafe automatic executions |
|---:|---:|---:|
| 0.50 | 3.7% | 9 |
| 0.55 | 2.5% | 7 |
| 0.60 | 1.1% | 4 |
| 0.65 | 0.2% | 2 |
| 0.70 | 0.0% | 0 |

The second seed preserves the same qualitative automation--safety trade-off.

## Paper Figures

The paper contains four generated figures:

```text
paper/figures/incident_distribution.png
paper/figures/auto_decision_progression.png
paper/figures/automation_vs_unsafe_execution_seed42.png
paper/figures/automation_vs_unsafe_execution_seed43.png
```

## Important Scientific Boundary

BGL provides incident-log frequency information, not remediation ground truth.
The benchmark therefore uses an explicit simulated incident-to-action mapping and fixed action outcome probabilities. The results demonstrate behavior of the implemented simulated gate and are not presented as production remediation effectiveness.

## Remaining External Deliverable

The Project Guide's final hand-over gate also requires a five-minute screen capture walking through one run. This cannot be generated from the repository audit itself and must be recorded and sent to the mentor separately.
