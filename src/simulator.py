from dataclasses import dataclass
import random

from .evidence import EvidenceStore


@dataclass(frozen=True)
class Incident:
    incident_id: str
    incident_type: str
    machine_class: str
    timestamp: str


@dataclass(frozen=True)
class Action:
    action_type: str
    reversibility: float
    blast_radius: float


class OutcomeType:
    RESOLVED = "resolved"
    RECURRED = "recurred"
    HARMFUL = "harmful"


@dataclass(frozen=True)
class Outcome:
    outcome_type: str
    action_type: str
    incident_type: str
    correct_action: str
    action_was_correct: bool


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

OUTCOME_PROBABILITIES = {
    "restart_service": (0.80, 0.15, 0.05),
    "requeue_job": (0.45, 0.35, 0.20),
    "reset_driver": (0.60, 0.25, 0.15),
    "drain_node": (0.50, 0.25, 0.25),
    "reclaim_disk": (0.40, 0.30, 0.30),
}

INCIDENT_ACTIONS = {
    "kernel_error": "reset_driver",
    "storage_error": "reclaim_disk",
    "filesystem_failure": "restart_service",
    "communication_failure": "drain_node",
    "application_error": "requeue_job",
}


def generate_incident(rng=None, incident_id="INC-000001"):
    rng = rng or random
    return Incident(
        incident_id=incident_id,
        incident_type=rng.choices(
            INCIDENT_TYPES,
            weights=INCIDENT_WEIGHTS,
            k=1,
        )[0],
        machine_class=rng.choice(MACHINE_CLASSES),
        timestamp="2026-09-07 22:30:00",
    )


def generate_incidents(count=1000, rng=None):
    if count < 0:
        raise ValueError("count must be non-negative")

    rng = rng or random

    return [
        generate_incident(
            rng=rng,
            incident_id=f"INC-{index + 1:06d}",
        )
        for index in range(count)
    ]


def get_correct_action(incident_type):
    return INCIDENT_ACTIONS[incident_type]


def is_correct_action(incident_type, action_type):
    return get_correct_action(incident_type) == action_type


def generate_outcome(incident_type, action_type, rng=None):
    rng = rng or random

    if incident_type not in INCIDENT_ACTIONS:
        raise KeyError(
            f"No ground-truth remediation configured for incident type: "
            f"{incident_type}"
        )

    if action_type not in OUTCOME_PROBABILITIES:
        raise KeyError(
            f"No outcome probabilities configured for action type: "
            f"{action_type}"
        )

    correct_action = get_correct_action(incident_type)
    action_was_correct = action_type == correct_action

    probabilities = OUTCOME_PROBABILITIES[action_type]

    outcome_type = rng.choices(
        [
            OutcomeType.RESOLVED,
            OutcomeType.RECURRED,
            OutcomeType.HARMFUL,
        ],
        weights=probabilities,
        k=1,
    )[0]

    return Outcome(
        outcome_type=outcome_type,
        action_type=action_type,
        incident_type=incident_type,
        correct_action=correct_action,
        action_was_correct=action_was_correct,
    )


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
    else:
        raise ValueError(
            f"Unknown outcome type: {outcome.outcome_type}"
        )