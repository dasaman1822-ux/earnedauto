import random

import matplotlib.pyplot as plt

from src.evidence import EvidenceStore
from src.gate import TrustGate
from src.simulator import (
    apply_outcome_to_evidence,
    generate_incident,
    generate_outcome,
)


EXPERIMENTS = [
    {
        "action_type": "restart_service",
        "incident_type": "kernel_error",
    },
    {
        "action_type": "drain_node",
        "incident_type": "communication_failure",
    },
]

MACHINE_CLASS = "compute_node"
TRIALS = 100


def run_action_experiment(
    action_type,
    incident_type,
    machine_class,
    trials,
    evidence_store,
):
    gate = TrustGate(evidence_store=evidence_store)

    decisions = []
    auto_proportion_history = []
    first_auto_incident = None

    for incident_number in range(1, trials + 1):
        incident = generate_incident()

        # Control the incident type so that the experiment evaluates
        # a known incident/action pairing rather than mixing correct
        # and incorrect remediation scenarios.
        incident.incident_type = incident_type

        result = gate.decide(
            action_type=action_type,
            machine_class=machine_class,
        )

        decisions.append(result.decision)

        # ESCALATE represents human-approved handling in this
        # learning experiment. The observed outcome contributes
        # evidence for the action and machine-class combination.
        outcome = generate_outcome(
            action_type=action_type,
            incident_type=incident.incident_type,
        )

        apply_outcome_to_evidence(
            outcome=outcome,
            action_type=action_type,
            machine_class=machine_class,
            evidence_store=evidence_store,
        )

        if result.decision == "AUTO" and first_auto_incident is None:
            first_auto_incident = incident_number

        auto_count = decisions.count("AUTO")
        auto_proportion_history.append(
            auto_count / incident_number
        )

    return (
        decisions,
        auto_proportion_history,
        first_auto_incident,
    )


def main():
    random.seed(42)

    results = {}

    for experiment in EXPERIMENTS:
        action_type = experiment["action_type"]
        incident_type = experiment["incident_type"]

        evidence_store = EvidenceStore()

        (
            decisions,
            auto_history,
            first_auto_incident,
        ) = run_action_experiment(
            action_type=action_type,
            incident_type=incident_type,
            machine_class=MACHINE_CLASS,
            trials=TRIALS,
            evidence_store=evidence_store,
        )

        results[action_type] = {
            "incident_type": incident_type,
            "decisions": decisions,
            "auto_history": auto_history,
            "first_auto_incident": first_auto_incident,
        }

        print()
        print("Action:", action_type)
        print("Incident type:", incident_type)
        print("Machine class:", MACHINE_CLASS)
        print("Decisions:")
        print("  ESCALATE:", decisions.count("ESCALATE"))
        print("  PROPOSE:", decisions.count("PROPOSE"))
        print("  AUTO:", decisions.count("AUTO"))

        if first_auto_incident is None:
            print("First AUTO decision: never")
        else:
            print(
                "First AUTO decision:",
                first_auto_incident,
            )

    plt.figure(figsize=(8, 5))

    for action_type, result in results.items():
        auto_history_percent = [
            value * 100
            for value in result["auto_history"]
        ]

        plt.plot(
            range(1, TRIALS + 1),
            auto_history_percent,
            label=action_type,
        )

        if result["first_auto_incident"] is not None:
            first_auto = result["first_auto_incident"]
            first_auto_value = (
                result["auto_history"][first_auto - 1] * 100
            )

            plt.scatter(
                first_auto,
                first_auto_value,
                zorder=3,
            )

            plt.annotate(
                f"First AUTO: incident {first_auto}",
                xy=(first_auto, first_auto_value),
                xytext=(
                    first_auto + 8,
                    first_auto_value + 5,
                ),
                arrowprops={"arrowstyle": "->"},
            )

    plt.xlabel("Simulated incident")
    plt.ylabel("AUTO decisions (%)")
    plt.title(
        "Proportion of AUTO Decisions Across Simulated Incidents"
    )
    plt.ylim(0, 100)
    plt.xlim(1, TRIALS)
    plt.yticks(range(0, 101, 10))
    plt.grid(
        axis="y",
        alpha=0.3,
    )
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "results/week3_auto_proportion.png",
        dpi=300,
    )

    plt.show()


if __name__ == "__main__":
    main()