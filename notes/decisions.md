# Design Decisions and Weekly Record

This file records the design decisions and implementation work completed so far.
The record is organized by project week so that the paper and repository history
can be traced back to the decisions made during development.

---

## Week 1 — Data Shape and Skeleton

### 1. Dataset Selection

The Blue Gene/L (BGL) public log dataset was selected to analyze the
distribution of infrastructure alerts.

The dataset provides a large collection of labelled infrastructure log records
and is used to inform the incident distribution implemented by the simulator.

The project does not use the dataset to train a machine-learning failure
detector.

### 2. Incident Taxonomy

The simulator uses five broad incident types:

- `kernel_error`
- `storage_error`
- `filesystem_failure`
- `communication_failure`
- `application_error`

A small set of broad categories was selected to keep the simulator simple,
interpretable, and manageable.

### 3. Machine Classes

The simulator represents three machine classes:

- `compute_node`
- `storage_node`
- `scheduler`

Machine class is included because remediation evidence should depend on the
context in which an action is used.

### 4. Incident Distribution

The simulator uses different probabilities for the five incident types rather
than equal probabilities.

These probabilities are informed by the alert distribution observed during the
BGL analysis.

The probabilities are simulation assumptions and are not treated as exact
ground-truth mappings between BGL labels and the simulator's incident
categories.

### 5. Incident Simulator

A simulator is used because the project does not operate a real infrastructure
cluster.

The simulator provides controlled incidents for evaluating the trust gate.

The initial Week 1 simulator focused on generating incidents and their
distribution. Outcome modelling was intentionally left for a later stage.

### 6. Incident IDs

The simulator assigns sequential incident IDs such as:

```text
INC-000001
INC-000002
INC-000003
```

Sequential identifiers make individual simulated incidents easier to distinguish
and trace during testing.

### 7. Initial Remediation Actions

The project models six remediation actions:

1. Restart a stateless service
2. Requeue a failed job
3. Reset a device driver
4. Drain a node and migrate work
5. Reclaim disk space by deleting temporary files
6. Escalate to a human

### 8. Raw Dataset Storage

The raw BGL dataset is kept outside the Git repository.

The repository contains the analysis script and documented results, while the
large raw dataset remains in the local project data directory.

### 9. Week 1 Result

The simulator produced 1,000 incidents and generated an incident distribution
plot. The plot was saved under `results/incident_distribution.png`.

---

## Week 2 — The Gate, First Version

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

The implementation also requires observed history before returning `AUTO`.
Therefore, an action with no previous outcome history cannot be automatically
executed.

### 2. Action Configuration

Reversibility and blast-radius values were placed in
`config/actions.yaml` rather than hard-coded into the gate.

Current values are:

| Action | Reversibility | Blast Radius |
|---|---:|---:|
| `restart_service` | 0.9 | 0.1 |
| `requeue_job` | 0.9 | 0.1 |
| `reset_driver` | 0.6 | 0.3 |
| `drain_node` | 0.5 | 0.7 |
| `reclaim_disk` | 0.3 | 0.5 |
| `escalate` | 1.0 | 0.0 |

These are engineering judgements used by the simulator and gate; they are not
measurements from the BGL dataset.

### 3. Threshold Configuration

The initial thresholds were placed in `config/thresholds.yaml`:

```text
AUTO_THRESHOLD = 0.65
PROPOSE_THRESHOLD = 0.35
RISK_CEILING = 0.60
```

These are initial engineering choices and are not presented as optimal values.

### 4. Bayesian Evidence Model

Each `(action_type, machine_class)` combination starts with a Beta(1, 1)
prior.

A successful outcome increments `alpha`.

A failed outcome increments `beta`.

The gate uses a conservative lower percentile of the Beta posterior rather than
the posterior mean.

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

This preserves context instead of allowing evidence from one machine class to
automatically transfer to another.

### 6. SciPy Decision

SciPy was added because the Week 2 gate requires a lower percentile of the Beta
posterior.

`scipy.stats.beta.ppf()` calculates the posterior percentile directly. This
avoids implementing a numerical inverse-CDF algorithm and keeps the evidence
calculation concise and readable.

### 7. Week 2 Tests

Five unit tests were implemented.

They verify that:

- an action with no history never returns `AUTO`;
- a high blast-radius action never returns `AUTO`;
- the gate can return `PROPOSE`;
- sufficient successful evidence can produce `AUTO`;
- the gate can return `ESCALATE`.

The test suite passed:

```text
5 passed
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

### 9. Week 2 Paper Update

The technical paper was updated to document:

- the Week 2 gate implementation;
- the Beta evidence model;
- the 5th-percentile lower bound;
- the five passing tests;
- the 1,000-incident verification;
- the decision-count table showing `0 AUTO`, `0 PROPOSE`, and `1000 ESCALATE`.

The updated paper PDF was committed to the repository.

---

## Week 3 — Outcomes and Learning

### 1. Outcome Types

Outcome modelling was added to the simulator.

Three outcome types are represented:

- `RESOLVED` — the action successfully resolves the incident.
- `RECURRED` — the action appears to work, but the incident returns.
- `HARMFUL` — the action makes the situation worse.

The `RECURRED` state explicitly represents the case where an action appears to
work but does not fix the underlying problem.

### 2. Action-Specific Outcome Probabilities

The simulator currently assigns different outcome probabilities to remediation
actions:

| Action | Resolved | Recurred | Harmful |
|---|---:|---:|---:|
| `restart_service` | 0.80 | 0.15 | 0.05 |
| `requeue_job` | 0.45 | 0.35 | 0.20 |
| `reset_driver` | 0.60 | 0.25 | 0.15 |
| `drain_node` | 0.50 | 0.25 | 0.25 |
| `reclaim_disk` | 0.40 | 0.30 | 0.30 |

These are simulator assumptions used to model different remediation reliability
profiles. They are not measurements from the BGL dataset.

### 3. Outcome-to-Evidence Feedback

Outcome results are now connected to the Beta evidence model through
`apply_outcome_to_evidence()`.

The mapping is:

```text
RESOLVED -> record_success()
RECURRED -> record_failure()
HARMFUL  -> record_failure()
```

Evidence remains scoped to `(action_type, machine_class)`.

### 4. Outcome Evidence Behaviour

A successful outcome changes the Beta evidence from:

```text
Beta(1, 1) -> Beta(2, 1)
```

A recurrent or harmful outcome increases the failure evidence through
`record_failure()`.

### 5. Simulator Verification

The updated simulator was run successfully and continued to generate 1,000
incidents with the existing incident distribution and sequential incident IDs.

### 6. Week 3 Status So Far

The outcome model and outcome-to-evidence update mechanism have been added.

The remaining Week 3 implementation is the complete learning loop in which
incidents pass through the gate, receive simulated outcomes, update evidence,
and then influence subsequent gate decisions.


