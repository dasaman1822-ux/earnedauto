# Design Decisions

## 1. Dataset Selection

The Blue Gene/L (BGL) public log dataset was selected to analyze the distribution of infrastructure alerts.

The dataset provides a large collection of labelled infrastructure log records and is used to inform the incident distribution implemented by the simulator.

The project does not use the dataset to train a machine-learning failure detector.

---

## 2. Incident Taxonomy

The simulator uses five broad incident types:

- `kernel_error`
- `storage_error`
- `filesystem_failure`
- `communication_failure`
- `application_error`

A small set of broad categories was selected for the initial simulator to keep the Week 1 implementation simple, interpretable, and manageable.

More detailed incident subtypes can be introduced later if they are required to model different remediation outcomes.

---

## 3. Machine Classes

The simulator currently represents three machine classes:

- `compute_node`
- `storage_node`
- `scheduler`

Machine class is included in the incident representation because remediation evidence should depend on the context in which an action is used.

---

## 4. Incident Distribution

The simulator uses different probabilities for the five incident types rather than assigning them equal probabilities.

These probabilities are informed by the alert distribution observed during the BGL analysis.

The probabilities are simulation assumptions and are not treated as exact ground-truth mappings between BGL labels and the simulator's incident categories.

---

## 5. Incident Simulator

A simulator is used because the project does not operate a real infrastructure cluster.

The simulator provides controlled incidents that can be used to evaluate the trust gate under repeatable conditions.

The simulator is intended to represent simplified incident patterns without attempting to reproduce the complete BGL dataset.

---

## 6. Incident IDs

The simulator assigns sequential incident IDs such as:

```text
INC-000001
INC-000002
INC-000003
```

Sequential identifiers make individual simulated incidents easier to distinguish and trace during testing and evaluation.

---

## 7. Outcome Modeling

The Week 1 simulator does not yet model remediation outcomes.

This is intentional because outcome modeling and evidence updates are part of the later project stages.

The initial simulator therefore focuses on generating incidents and their distribution.

---

## 8. Paper Format

The technical paper is being written in Markdown.

Markdown was selected because the project guide permits either LaTeX or plain Markdown and recommends selecting one format during Week 1 and maintaining that format throughout the project.

---

## 9. Raw Dataset Storage

The raw BGL dataset is kept outside the Git repository.

The repository contains the analysis script and documented results, while the large raw dataset remains in the local project data directory.

This avoids unnecessarily storing the large raw log file in the project repository.

---

## 10. Initial Remediation Actions

The simulator defines six remediation actions:

1. Restart a stateless service
2. Requeue a failed job
3. Reset a device driver
4. Drain a node and migrate work
5. Reclaim disk space by deleting temporary files
6. Escalate to a human

Each action has initial reversibility and blast-radius values that will be used by the trust gate.

---

## 11. SciPy Dependency for Beta Confidence Bounds

SciPy was added to the project because the Week 2 gate requires a lower percentile of the Beta posterior.

The implementation uses `scipy.stats.beta.ppf()` to calculate this posterior percentile directly.

This avoids implementing a numerical inverse-CDF algorithm for the Beta distribution and keeps the evidence calculation concise and readable.

SciPy is therefore used specifically for the Beta posterior lower-bound calculation in `src/evidence.py`.