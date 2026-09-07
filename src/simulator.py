from dataclasses import dataclass
from collections import Counter
import random
import matplotlib.pyplot as plt

@dataclass
class Incident:
    incident_id: str
    incident_type: str
    machine_class: str
    timestamp: str


@dataclass
class Action:
    action_type: str
    reversibility: float
    blast_radius: float


ACTIONS = [
    Action("restart_service", 0.9, 0.1),
    Action("requeue_job", 0.9, 0.1),
    Action("reset_driver", 0.6, 0.3),
    Action("drain_node", 0.5, 0.7),
    Action("reclaim_disk", 0.3, 0.5),
    Action("escalate", 1.0, 0.0),
]


INCIDENT_TYPES = [
    "kernel_error",
    "storage_error",
    "filesystem_failure",
    "communication_failure",
    "application_error",
]


MACHINE_CLASSES = [
    "compute_node",
    "storage_node",
    "scheduler",
]


def generate_incident():
    incident_type = random.choice(INCIDENT_TYPES)
    machine_class = random.choice(MACHINE_CLASSES)

    return Incident(
        incident_id=f"INC-{random.randint(1, 999999):06d}",
        incident_type=incident_type,
        machine_class=machine_class,
        timestamp="2026-09-07 22:30:00",
    )


def generate_incidents(count=1000):
    return [generate_incident() for _ in range(count)]


if __name__ == "__main__":
    incidents = generate_incidents(1000)

    print(f"Generated {len(incidents)} incidents")

    incident_counts = Counter(
        incident.incident_type for incident in incidents
    )

    print(incident_counts)

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