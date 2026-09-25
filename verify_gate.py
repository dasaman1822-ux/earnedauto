from collections import Counter

from src.gate import TrustGate
from src.simulator import generate_incidents


def main():
    """Run 1,000 simulated incidents through the trust gate."""
    incidents = generate_incidents(1000)
    gate = TrustGate()

    decisions = Counter()
    rows = []

    action_types = [
        "restart_service",
        "requeue_job",
        "reset_driver",
        "drain_node",
        "reclaim_disk",
        "escalate",
    ]

    for index, incident in enumerate(incidents):
        action_type = action_types[index % len(action_types)]

        result = gate.decide(
            action_type=action_type,
            machine_class=incident.machine_class,
        )

        decisions[result.decision] += 1

        rows.append(
            (
                incident.incident_id,
                incident.incident_type,
                incident.machine_class,
                action_type,
                result.decision,
                result.reversibility,
                result.blast_radius,
                result.evidence_lower_bound,
                result.trust,
                result.risk,
            )
        )

    print(f"Generated incidents: {len(incidents)}")

    print("\nDecision counts:")
    for decision in ["AUTO", "PROPOSE", "ESCALATE"]:
        print(f"{decision}: {decisions[decision]}")

    print("\nFirst 20 decisions:")
    print(
        "INCIDENT_ID | INCIDENT_TYPE | MACHINE_CLASS | "
        "ACTION | DECISION | TRUST | RISK"
    )

    for row in rows[:20]:
        (
            incident_id,
            incident_type,
            machine_class,
            action_type,
            decision,
            reversibility,
            blast_radius,
            evidence_lower_bound,
            trust,
            risk,
        ) = row

        print(
            f"{incident_id} | "
            f"{incident_type} | "
            f"{machine_class} | "
            f"{action_type} | "
            f"{decision} | "
            f"{trust:.3f} | "
            f"{risk:.3f}"
        )


if __name__ == "__main__":
    main()