# Design Decisions and Weekly Record

This file records the design decisions and weekly implementation work completed so far.

---

## Week 1 — Data Shape and Skeleton

### 1. Dataset Selection

The Blue Gene/L (BGL) public log dataset was selected to analyze the distribution of infrastructure alerts.

The dataset is used to inform the incident distribution implemented by the simulator. The project does not use the dataset to train a machine-learning failure detector.

### 2. Incident Taxonomy

The simulator uses five incident types:

- `kernel_error`
- `storage_error`
- `filesystem_failure`
- `communication_failure`
- `application_error`

### 3. Machine Classes

The simulator represents three machine classes:

- `compute_node`
- `storage_node`
- `scheduler`

Machine class is included because remediation evidence depends on the context in which an action is used.

### 4. Incident Distribution

The simulator uses different probabilities for the five incident types rather than equal probabilities.

These probabilities are informed by the alert distribution observed during the BGL analysis.

The probabilities are simulation assumptions and are not treated as exact ground truth mappings between BGL labels and the simulator's incident categories.

### 5. Incident Simulator

A simulator is used because the project does not operate a real infrastructure cluster.

The simulator provides controlled incidents for evaluating the trust gate.

### 6. Incident IDs

The simulator assigns sequential incident IDs such as:

```text
INC-000001
INC-000002
INC-000003
```

Sequential identifiers make individual simulated incidents easier to distinguish and trace during testing.

### 7. Remediation Actions

The project models six remediation actions:

1. Restart a stateless service
2. Requeue a failed job
3. Reset a device driver
4. Drain a node and migrate work
5. Reclaim disk space by deleting temporary files
6. Escalate to a human

### 8. Raw Dataset Storage

The raw BGL dataset is kept outside the Git repository.

The repository contains the analysis script and documented results, while the large raw dataset remains in the local project data directory.

### 9. Week 1 Result

The simulator produced 1,000 incidents and generated an incident distribution plot saved under:

```text
results/incident_distribution.png
```

---

## Week 2 — The Gate

### 1. Three-Factor Trust Gate

The gate uses three factors:

- reversibility
- blast radius
- accumulated evidence

The core calculation is:

```text
trust = reversibility * evidence_lower_bound
risk = normalised_blast_radius
```

The decision rule is:

```text
if trust > AUTO_THRESHOLD and risk < RISK_CEILING:
    AUTO
elif trust > PROPOSE_THRESHOLD:
    PROPOSE
else:
    ESCALATE
```

The implementation also requires observed history before returning `AUTO`. Therefore, an action with no previous outcome history cannot be automatically executed.

### 2. Action Configuration

Reversibility and blast-radius values are stored in `config/actions.yaml`.

Current values are:

| Action | Reversibility | Blast Radius |
|---|---:|---:|
| `restart_service` | 0.9 | 0.1 |
| `requeue_job` | 0.9 | 0.1 |
| `reset_driver` | 0.6 | 0.3 |
| `drain_node` | 0.5 | 0.7 |
| `reclaim_disk` | 0.3 | 0.5 |
| `escalate` | 1.0 | 0.0 |

These are engineering judgements used by the simulator and gate; they are not measurements from the BGL dataset.

### 3. Threshold Configuration

The initial thresholds are stored in `config/thresholds.yaml`:

```text
AUTO_THRESHOLD = 0.65
PROPOSE_THRESHOLD = 0.35
RISK_CEILING = 0.60
```

These are initial engineering choices and are not presented as optimal values.

### 4. Bayesian Evidence Model

Each `(action_type, machine_class)` combination starts with a Beta(1, 1) prior.

A successful outcome increments `alpha`.

A failed outcome increments `beta`.

The gate uses a conservative lower percentile of the Beta posterior rather than the posterior mean.

The current lower percentile is the 5th percentile:

```text
E_LB = Beta(alpha, beta) inverse CDF at 0.05
```

This is calculated using `scipy.stats.beta.ppf()` in `src/evidence.py`.

### 5. Evidence Context

Evidence is tracked separately for each:

```text
(action_type, machine_class)
```

This preserves context instead of allowing evidence from one machine class to automatically transfer to another.

### 6. SciPy Decision

SciPy was selected because the Week 2 gate requires a lower percentile of the Beta posterior.

`scipy.stats.beta.ppf()` calculates the posterior percentile directly. This avoids implementing a numerical inverse-CDF algorithm and keeps the evidence calculation concise and reproducible.

### 7. Week 2 Tests

Unit tests verify that:

- an action with no history never returns `AUTO`;
- a high blast-radius action never returns `AUTO`;
- the gate can return `PROPOSE`;
- sufficient successful evidence can produce `AUTO`;
- the gate can return `ESCALATE`.

The full test suite subsequently passed with:

```text
13 passed
```

### 8. Week 2 — 1,000 Incident Verification

The 1,000-incident check ran successfully.

Because no outcome history existed at this stage, the result was:

```text
AUTO: 0
PROPOSE: 0
ESCALATE: 1000
```

This was expected because the no-history safety condition prevents `AUTO`.

---

## Week 3 — Outcomes and Learning

### 1. Outcome Types

Three outcome types are represented:

- `RESOLVED` — the action successfully resolves the incident.
- `RECURRED` — the action appears to work, but the incident returns.
- `HARMFUL` — the action makes the situation worse.

The `RECURRED` state explicitly represents the case where an action appears to work but does not fix the underlying problem.

### 2. Action-Specific Outcome Probabilities

The simulator currently assigns different outcome probabilities to remediation actions:

| Action | Resolved | Recurred | Harmful |
|---|---:|---:|---:|
| `restart_service` | 0.80 | 0.15 | 0.05 |
| `requeue_job` | 0.45 | 0.35 | 0.20 |
| `reset_driver` | 0.60 | 0.25 | 0.15 |
| `drain_node` | 0.50 | 0.25 | 0.25 |
| `reclaim_disk` | 0.40 | 0.30 | 0.30 |

These are simulator assumptions used to model different remediation reliability profiles. They are not measurements from the BGL dataset.

### 3. Outcome-to-Evidence Feedback

Outcome results are connected to the Beta evidence model through `apply_outcome_to_evidence()`.

The mapping is:

```text
RESOLVED -> record_success()
RECURRED -> record_failure()
HARMFUL  -> record_failure()
```

Evidence remains scoped to `(action_type, machine_class)`.

### 4. Ground-Truth Remediation Mapping

The simulator defines an explicit ground-truth remediation mapping:

```text
kernel_error           -> reset_driver
storage_error          -> reclaim_disk
filesystem_failure     -> restart_service
communication_failure  -> drain_node
application_error      -> requeue_job
```

The candidate action is compared with this mapping and the resulting `action_was_correct` value is retained in the simulated outcome.

The action-level outcome probabilities remain fixed simulator assumptions and are not tuned to improve benchmark results.

### 5. Learning Experiment

The learning experiment demonstrates evidence accumulation for a known incident/action pairing.

For `restart_service`, `kernel_error`, and `compute_node`:

```text
ESCALATE: 3
PROPOSE: 50
AUTO: 47
```

The first `AUTO` decision occurred at incident 16.

For `drain_node`, `communication_failure`, and `compute_node`:

```text
ESCALATE: 100
PROPOSE: 0
AUTO: 0
```

The generated chart is stored as:

```text
results/auto_decision_progression.png
```

---

## Benchmark and Evaluation

### 1. Benchmark Design

The benchmark compares:

- Always Ask
- Always Act
- EarnedAutonomy

using:

- automatic resolution rate;
- mean time to recovery;
- human interruptions;
- unsafe automatic executions.

The benchmark uses deterministic seeds.

Seed 42 is the primary benchmark run and seed 43 is used for sensitivity analysis.

### 2. Seed 42 Results

| Metric | Always Ask | Always Act | EarnedAutonomy |
|---|---:|---:|---:|
| Automation rate | 0.0% | 100.0% | 0.2% |
| Automatic resolution rate | 0.0% | 52.8% | 0.0% |
| Mean time to recovery | 291.685 s | 171.685 s | 443.905 s |
| Human interruptions | 1000 | 472 | 1000 |
| Unsafe automatic executions | 0 | 472 | 2 |

### 3. Seed 43 Results

| Metric | Always Ask | Always Act | EarnedAutonomy |
|---|---:|---:|---:|
| Automation rate | 0.0% | 100.0% | 1.1% |
| Automatic resolution rate | 0.0% | 53.8% | 1.1% |
| Mean time to recovery | 288.300 s | 168.300 s | 442.320 s |
| Human interruptions | 1000 | 462 | 989 |
| Unsafe automatic executions | 0 | 462 | 0 |

### 4. Benchmark Interpretation

The results show that EarnedAutonomy is substantially more conservative than Always Act.

The results do not demonstrate that EarnedAutonomy dominates either baseline.

Instead, the benchmark demonstrates the trade-off between conservative evidence-gated autonomy and more aggressive automation policies.

### 5. Documented Limitations

The benchmark identifies several conditions where EarnedAutonomy performs no better than a baseline.

In the seed-42 experiment, EarnedAutonomy produced two unsafe automatic executions while Always Ask produced none. EarnedAutonomy therefore does not provide a safety improvement over Always Ask in that run.

EarnedAutonomy also had the highest mean time to recovery in both benchmark runs:

```text
Seed 42:
Always Ask      291.685 s
Always Act      171.685 s
EarnedAutonomy  443.905 s

Seed 43:
Always Ask      288.300 s
Always Act      168.300 s
EarnedAutonomy  442.320 s
```

EarnedAutonomy achieved very low automation:

```text
Seed 42: 0.2%
Seed 43: 1.1%
```

compared with 100% automation for Always Act.

These results indicate that the current gate prioritises conservative decision-making at the cost of automation and recovery latency.

### 6. Reproducibility

The benchmark was executed repeatedly with the same seed.

Running the benchmark twice with seed 42 produced identical output:

```text
FC: no differences encountered
```

This confirms deterministic behaviour for the benchmark configuration.

---

## Threshold Sensitivity

### 1. Sweep Design

The threshold sweep evaluates combinations of AUTO and PROPOSE thresholds.

Configurations where the PROPOSE threshold is greater than or equal to the AUTO threshold are excluded.

Each seed produced exactly 69 valid threshold configurations.

### 2. Seed 42 Sweep

The highest observed automation rate was:

```text
Automation rate: 3.7%
AUTO threshold: 0.5
PROPOSE threshold: 0.2
Unsafe automatic executions: 9
Unsafe automatic execution rate: 24.3243%
```

### 3. Seed 43 Sweep

The highest observed automation rate was:

```text
Automation rate: 3.9%
AUTO threshold: 0.5
PROPOSE threshold: 0.2
Unsafe automatic executions: 5
Unsafe automatic execution rate: 12.8205%
```

### 4. Sweep Interpretation

The threshold sweep demonstrates the trade-off between increased autonomy and unsafe automatic execution.

The sweep is treated as sensitivity analysis rather than as a mechanism for selecting thresholds solely to maximise automation.

Generated files:

```text
results/threshold_sweep_seed42.json
results/threshold_sweep_seed43.json
results/automation_vs_unsafe_execution_seed42.png
results/automation_vs_unsafe_execution_seed43.png
results/threshold_sweep_summary_seed42.md
results/threshold_sweep_summary_seed43.md
```

---

## Scientific Boundary

The BGL dataset is used to inform incident-type frequency only.

It does not provide remediation ground truth for the simulator.

The benchmark therefore uses an explicit simulated incident-to-action mapping and fixed action outcome probabilities.

These assumptions are documented rather than presented as measurements from BGL or production infrastructure.

The simulator records whether the candidate action matches the configured ground-truth remediation mapping, but the current benchmark candidate-action policy selects the configured remediation action for each incident type.

The simulator therefore should not be described as a learned remediation model.

---

## Logging and Evaluation Records

The benchmark records the fields required to evaluate the gate, including:

- timestamp;
- incident identifier;
- incident type;
- candidate action;
- machine class;
- reversibility;
- blast radius;
- evidence lower bound;
- decision;
- outcome;
- resolution status;
- recovery time.

This supports reproducibility and post-run analysis.

---

## Drain Approach

The project adopts the published Drain log-template extraction approach rather than implementing a full custom log parser.

The approach uses a fixed-depth parse tree, token similarity, and wildcard template generalisation.

A small deterministic in-repository implementation is used to keep the project CPU-only and reproducible without adding a parser service.

The template miner is applied to a bounded sample of BGL messages, while the full dataset is scanned for exact label frequencies.

---

## Current Results Directory

The current `results` directory contains:

```text
automation_vs_unsafe_execution_seed42.png
automation_vs_unsafe_execution_seed43.png
auto_decision_progression.png
benchmark_results.json
benchmark_results_seed42.json
benchmark_results_seed43.json
benchmark_summary.md
benchmark_summary_seed42.md
benchmark_summary_seed43.md
incident_distribution.png
threshold_sweep_seed42.json
threshold_sweep_seed43.json
threshold_sweep_summary_seed42.md
threshold_sweep_summary_seed43.md
```

---

## Final Repository Status

The implemented project currently includes:

- incident simulation;
- BGL-informed incident distribution;
- five incident types;
- three machine classes;
- six remediation actions;
- reversibility and blast-radius modelling;
- Beta evidence tracking;
- SciPy Beta posterior lower-confidence bounds;
- three-factor trust gating;
- outcome simulation;
- evidence feedback;
- ground-truth remediation mapping;
- deterministic benchmarking;
- Always Ask baseline;
- Always Act baseline;
- EarnedAutonomy benchmark;
- threshold sensitivity analysis;
- automation-versus-unsafe-execution plots;
- learning progression visualization;
- unit tests;
- reproducibility verification;
- documentation of benchmark limitations.

The remaining finalisation work is to keep the technical paper synchronized with these implementation results, perform the final Project Guide field-by-field audit, clean the repository, and complete the required five-minute screen capture.
