# Earned Autonomy: A Reversibility and Evidence Gate for Automated Infrastructure Remediation

## 1. Introduction

Modern infrastructure systems can detect failures and perform automated remediation actions. Automation can reduce recovery time and the amount of work required from human operators. However, automatically performing an incorrect remediation can make an incident worse.

This project explores a trust gate for automated infrastructure remediation. The gate decides whether a remediation action should be **AUTO**, **PROPOSE**, or **ESCALATE**.

The decision considers three main factors: the **reversibility** of the action, its **blast radius**, and accumulated **evidence** about whether the action is successful in a particular context.

The central idea is **earned autonomy**. An action should gain permission to operate automatically as evidence of successful behavior accumulates. If the action fails, its level of autonomy should be reduced.

---

## 2. Problem Statement

A self-healing infrastructure system needs to balance automation and safety. A highly automated system can reduce recovery time, but automatically executing an incorrect action can cause additional damage.

The project therefore asks:

> How can a remediation system decide when it has enough evidence and sufficiently low risk to perform an action automatically?

The proposed trust gate provides three possible decisions:

- **AUTO** — execute the action automatically.
- **PROPOSE** — recommend the action but require human approval.
- **ESCALATE** — require human intervention.

---

## 3. Project Scope

The project focuses on the decision-making layer between fault detection and remediation execution.

The project does not build a monitoring system, dashboard, or machine-learning failure detector. Instead, a simulator is used to generate infrastructure incidents and provide a controlled environment for evaluating the trust gate.

The project considers six remediation actions:

1. Restart a stateless service
2. Requeue a failed job
3. Reset a device driver
4. Drain a node and migrate work
5. Reclaim disk space by deleting temporary files
6. Escalate to a human

The simulator is used to evaluate whether the trust gate can support automation while limiting unsafe automatic actions.

---

## 4. Dataset and Incident Analysis

The Blue Gene/L (BGL) public log dataset was selected to understand real infrastructure incident patterns.

The analysis identified:

- **4,747,963** total log records
- **4,399,503** normal records
- **348,460** alert records
- **7.34%** alert records
- **42** distinct alert labels

The most frequent alert labels included `KERNDTLB`, `KERNSTOR`, `APPSEV`, `KERNMNTF`, and `KERNTERM`.

A Python script, `src/analyze_bgl.py`, was created to read the BGL log and count the labels.

The BGL dataset is used only to understand the distribution of infrastructure alerts and to inform the simulator. The simulator does not attempt to reproduce all 42 BGL labels directly.

---

## 5. Incident and Action Data Structures

Two simple data classes were created for the simulator.

### 5.1 Incident

Each incident contains:

- Incident ID
- Incident type
- Machine class
- Timestamp

Example:

```text
INC-000001
storage_error
storage_node
2026-09-07 22:30:00
```

### 5.2 Action

Each remediation action contains:

- Action type
- Reversibility
- Blast radius

Reversibility represents how easily an action can be undone. Blast radius represents the extent of the system that may be affected if the action is incorrect.

The initial actions are:

| Action | Reversibility | Blast Radius |
|---|---:|---:|
| Restart service | 0.9 | 0.1 |
| Requeue job | 0.9 | 0.1 |
| Reset driver | 0.6 | 0.3 |
| Drain node | 0.5 | 0.7 |
| Reclaim disk | 0.3 | 0.5 |
| Escalate | 1.0 | 0.0 |

These values are maintained in `config/actions.yaml`.

---

## 6. Incident Simulator

A Python-based incident simulator was implemented to generate infrastructure incidents for evaluating the trust gate.

The simulator uses five broad incident types:

- `kernel_error`
- `storage_error`
- `filesystem_failure`
- `communication_failure`
- `application_error`

It also represents three machine classes:

- `compute_node`
- `storage_node`
- `scheduler`

The simulator can generate 1,000 incidents in a single run. Each incident is assigned a unique sequential identifier.

The simulator currently focuses on generating incident data and its distribution. Remediation outcomes are not yet modeled because outcome modeling is part of the next project stage.

### 6.1 Incident Distribution

The simulator uses different probabilities for the five incident types rather than assigning equal probabilities.

The current simulation weights are:

| Incident Type | Weight |
|---|---:|
| Kernel error | 52.35% |
| Storage error | 18.31% |
| Filesystem failure | 9.30% |
| Communication failure | 1.77% |
| Application error | 18.27% |

These values are simulation assumptions informed by the BGL analysis. They are not treated as exact ground-truth mappings from BGL labels to the simulator's incident categories.

The simulator generates 1,000 incidents, counts the incident categories, and produces a distribution plot.

The generated plot is saved as:

```text
results/incident_distribution.png
```

---

## 7. Week 2: Trust Gate Design and Implementation

The second stage of the project implemented the first version of the trust gate.

The gate determines whether a candidate remediation action should be:

```text
AUTO
PROPOSE
ESCALATE
```

The decision is based on three factors:

- Reversibility
- Blast radius
- Accumulated evidence

### 7.1 Reversibility

Reversibility measures how easily an action can be undone if it is incorrect.

The values are normalized between 0 and 1 and are stored in `config/actions.yaml`.

Higher values represent actions that are easier to reverse.

### 7.2 Blast Radius

Blast radius represents the extent of system impact if an action is incorrect.

The values are normalized between 0 and 1 and are also stored in `config/actions.yaml`.

A larger blast radius increases the risk associated with automatic execution.

### 7.3 Bayesian Evidence

The evidence component uses a Beta posterior.

Each action and machine-class combination begins with a Beta(1,1) prior.

A successful remediation increments `alpha` by one:

```text
alpha = alpha + 1
```

A failed remediation increments `beta` by one:

```text
beta = beta + 1
```

Evidence is tracked separately for each:

```text
(action_type, machine_class)
```

combination.

This provides context-specific evidence without tracking each individual machine separately.

The implementation uses the 5th percentile of the Beta posterior as a lower-bound estimate rather than using the posterior mean.

SciPy is used through:

```text
scipy.stats.beta.ppf()
```

to calculate this posterior percentile directly.

### 7.4 Trust and Risk

The trust and risk values are calculated as:

```text
trust = reversibility * evidence_lower_bound
risk = normalised_blast_radius
```

The initial thresholds are stored in `config/thresholds.yaml`:

```text
AUTO_THRESHOLD = 0.65
PROPOSE_THRESHOLD = 0.35
RISK_CEILING = 0.60
```

The decision rule is:

```text
if trust > AUTO_THRESHOLD
and risk < RISK_CEILING:
    AUTO

elif trust > PROPOSE_THRESHOLD:
    PROPOSE

else:
    ESCALATE
```

The implementation also requires previous outcome history before allowing an `AUTO` decision. This prevents an action with no observed outcomes from immediately receiving automatic execution permission.

The risk ceiling prevents an action at or above the configured blast-radius ceiling from receiving an `AUTO` decision.

### 7.5 Safety Tests

Unit tests were added for the required safety conditions.

The first test verifies that an action with no previous outcome history never returns `AUTO`.

The second test verifies that a high blast-radius action does not return `AUTO`, even after successful observations.

Additional tests verify that the gate can produce all three decision states:

```text
AUTO
PROPOSE
ESCALATE
```

The complete test suite contains five tests, and all five tests passed.

### 7.6 Week 2 End-to-End Check

The gate was executed on 1,000 simulated incidents.

The resulting decision counts were:

| Decision | Count |
|---|---:|
| AUTO | 0 |
| PROPOSE | 0 |
| ESCALATE | 1,000 |

This result is expected at this stage because the simulator does not yet provide remediation outcomes.

Without previous evidence, the gate conservatively keeps the decisions at `ESCALATE`.

Outcome modelling and evidence learning will be introduced in the next project stage.

---

## 8. Week 1 and Week 2 Progress

The project now contains the initial simulator and the first implementation of the trust gate.

The completed components include:

- Project repository and folder structure
- BGL dataset analysis
- Incident and action data classes
- Incident simulator
- Five broad incident types
- Three machine classes
- Six remediation actions
- Generation of 1,000 incidents
- Incident distribution visualization
- Configurable reversibility and blast-radius values
- Configurable trust-gate thresholds
- Beta posterior evidence tracking
- Context-specific evidence by action type and machine class
- `AUTO`, `PROPOSE`, and `ESCALATE` decisions
- Required Week 2 safety tests
- 1,000-incident end-to-end gate check

---

## 9. Next Stage

The next stage will add remediation outcomes to the simulator and feed those outcomes back into the evidence store.

The simulator will include:

- Correct actions that resolve incidents
- Actions that appear to work but do not resolve the underlying cause
- Rare harmful actions

This will allow the project to evaluate whether remediation actions can earn increasing autonomy as successful evidence accumulates, while losing autonomy when failures are observed.