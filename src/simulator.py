from dataclasses import dataclass
from collections import Counter
import random

import matplotlib.pyplot as plt

from src.evidence import EvidenceStore


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    machine_class: str
    timestamp: str


class OutcomeType:
    RESOLVED = "resolved"
    RECURRED = "recurred"
    HARMFUL = "harmful"


@dataclass
class Outcome:
    outcome_type: str


INCIDENT_TYPES = [
    "kernel_error",
    "storage_error",
    "filesystem_failure",
    "communication_failure",
    "application_error",
]


INCIDENT_WEIGHTS = [
    0.5235,
    0.1831,
    0.0930,
    0.0177,
    0.1827,
]


MACHINE_CLASSES = [
    "compute_node",
    "storage_node",
    "scheduler",
]


CORRECT_ACTIONS = {
    "kernel_error": "restart_service",
    "storage_error": "reclaim_disk",
    "filesystem_failure": "reclaim_disk",
    "communication_failure": "drain_node",
    "application_error": "requeue_job",
}


def generate_incident():
    incident_type = random.choices(
        INCIDENT_TYPES,
        weights=INCIDENT_WEIGHTS,
        k=1,
    )[0]

    machine_class = random.choice(MACHINE_CLASSES)

    return Incident(
        incident_id=f"INC-{random.randint(1, 999999):06d}",
        incident_type=incident_type,
        machine_class=machine_class,
        timestamp="2026-09-07 22:30:00",
    )


def generate_outcome(action_type, incident_type=None):
    """
    Generate an outcome for a candidate remediation action.

    When incident_type is provided, the simulator distinguishes between
    the known correct remediation and an incorrect candidate action.

    These probabilities are fixed simulator assumptions, not measurements
    from the BGL dataset.
    """

    if incident_type is not None:
        correct_action = CORRECT_ACTIONS[incident_type]

        if action_type == correct_action:
            outcome_probabilities = (0.80, 0.15, 0.05)
        else:
            outcome_probabilities = (0.10, 0.75, 0.15)
    else:
        # Backward-compatible behavior for existing callers.
        outcome_probabilities = {
            "restart_service": (0.80, 0.15, 0.05),
            "requeue_job": (0.45, 0.35, 0.20),
            "reset_driver": (0.60, 0.25, 0.15),
            "drain_node": (0.50, 0.25, 0.25),
            "reclaim_disk": (0.40, 0.30, 0.30),
        }[action_type]

    resolved_probability, recurred_probability, harmful_probability = (
        outcome_probabilities
    )

    outcome_type = random.choices(
        [
            OutcomeType.RESOLVED,
            OutcomeType.RECURRED,
            OutcomeType.HARMFUL,
        ],
        weights=[
            resolved_probability,
            recurred_probability,
            harmful_probability,
        ],
        k=1,
    )[0]

    return Outcome(outcome_type=outcome_type)


def apply_outcome_to_evidence(
    outcome,
    action_type,
    machine_class,
    evidence_store,
):
    if outcome.outcome_type == OutcomeType.RESOLVED:
        evidence_store.record_success(
            action_type,
            machine_class,
        )

    elif outcome.outcome_type in (
        OutcomeType.RECURRED,
        OutcomeType.HARMFUL,
    ):
        evidence_store.record_failure(
            action_type,
            machine_class,
        )


def generate_incidents(count=1000):
    incidents = []

    for i in range(count):
        incident = generate_incident()
        incident.incident_id = f"INC-{i + 1:06d}"
        incidents.append(incident)

    return incidents


if __name__ == "__main__":
    incidents = generate_incidents(1000)

    print(f"Generated {len(incidents)} incidents")

    incident_counts = Counter(
        incident.incident_type for incident in incidents
    )

    print(incident_counts)
    print(incidents[:5])

    plt.bar(
        incident_counts.keys(),
        incident_counts.values(),
    )

    plt.xlabel("Incident Type")
    plt.ylabel("Count")
    plt.title("Simulated Incident Distribution")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("results/incident_distribution.png")
    plt.show()