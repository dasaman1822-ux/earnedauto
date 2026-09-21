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