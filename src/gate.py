from dataclasses import dataclass
from pathlib import Path

import yaml

from .evidence import EvidenceStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ACTIONS_CONFIG = PROJECT_ROOT / "config" / "actions.yaml"
THRESHOLDS_CONFIG = PROJECT_ROOT / "config" / "thresholds.yaml"


@dataclass(frozen=True)
class GateResult:
    """Result produced by the trust gate."""

    decision: str
    reversibility: float
    blast_radius: float
    evidence_lower_bound: float
    trust: float
    risk: float
    has_history: bool


class TrustGate:
    """
    Trust gate for automated infrastructure remediation.

    The gate combines:
    - reversibility
    - blast radius
    - accumulated evidence

    to produce:
    - AUTO
    - PROPOSE
    - ESCALATE
    """

    def __init__(
        self,
        actions_config: Path = ACTIONS_CONFIG,
        thresholds_config: Path = THRESHOLDS_CONFIG,
        evidence_store: EvidenceStore | None = None,
        evidence_percentile: float = 0.05,
    ) -> None:
        self.actions = self._load_yaml(actions_config)
        self.thresholds = self._load_yaml(thresholds_config)
        self.evidence = evidence_store or EvidenceStore()
        self.evidence_percentile = evidence_percentile

        self._validate_configuration()

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        """Load a YAML configuration file."""
        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {path}"
            )

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuration file must contain a mapping: {path}"
            )

        return data

    def _validate_configuration(self) -> None:
        """Validate action and threshold configuration."""
        if "actions" not in self.actions:
            raise ValueError(
                "actions.yaml must contain an 'actions' section."
            )

        required_thresholds = {
            "AUTO_THRESHOLD",
            "PROPOSE_THRESHOLD",
            "RISK_CEILING",
        }

        missing_thresholds = (
            required_thresholds - self.thresholds.keys()
        )

        if missing_thresholds:
            raise ValueError(
                "Missing thresholds: "
                + ", ".join(sorted(missing_thresholds))
            )

        auto_threshold = float(
            self.thresholds["AUTO_THRESHOLD"]
        )
        propose_threshold = float(
            self.thresholds["PROPOSE_THRESHOLD"]
        )
        risk_ceiling = float(
            self.thresholds["RISK_CEILING"]
        )

        if not 0 <= propose_threshold <= 1:
            raise ValueError(
                "PROPOSE_THRESHOLD must be between 0 and 1."
            )

        if not 0 <= auto_threshold <= 1:
            raise ValueError(
                "AUTO_THRESHOLD must be between 0 and 1."
            )

        if propose_threshold >= auto_threshold:
            raise ValueError(
                "PROPOSE_THRESHOLD must be lower than "
                "AUTO_THRESHOLD."
            )

        if not 0 <= risk_ceiling <= 1:
            raise ValueError(
                "RISK_CEILING must be between 0 and 1."
            )

        for action_type, config in self.actions["actions"].items():
            if "reversibility" not in config:
                raise ValueError(
                    f"Missing reversibility for '{action_type}'."
                )

            if "blast_radius" not in config:
                raise ValueError(
                    f"Missing blast_radius for '{action_type}'."
                )

            reversibility = float(config["reversibility"])
            blast_radius = float(config["blast_radius"])

            if not 0 <= reversibility <= 1:
                raise ValueError(
                    f"Reversibility for '{action_type}' "
                    "must be between 0 and 1."
                )

            if not 0 <= blast_radius <= 1:
                raise ValueError(
                    f"Blast radius for '{action_type}' "
                    "must be between 0 and 1."
                )

    def decide(
        self,
        action_type: str,
        machine_class: str,
    ) -> GateResult:
        """
        Evaluate an action in a machine-class context.

        The decision rule is:

        trust = reversibility * evidence_lower_bound
        risk = normalised_blast_radius

        if trust > AUTO_THRESHOLD
        and risk < RISK_CEILING
        and there is history:
            AUTO

        elif trust > PROPOSE_THRESHOLD:
            PROPOSE

        else:
            ESCALATE
        """
        actions = self.actions["actions"]

        if action_type not in actions:
            raise ValueError(
                f"Unknown action type: {action_type}"
            )

        action_config = actions[action_type]

        reversibility = float(
            action_config["reversibility"]
        )

        blast_radius = float(
            action_config["blast_radius"]
        )

        risk = blast_radius

        has_history = self.evidence.has_history(
            action_type,
            machine_class,
        )

        evidence_lower_bound = self.evidence.get_lower_bound(
            action_type,
            machine_class,
            self.evidence_percentile,
        )

        trust = (
            reversibility * evidence_lower_bound
        )

        auto_threshold = float(
            self.thresholds["AUTO_THRESHOLD"]
        )

        propose_threshold = float(
            self.thresholds["PROPOSE_THRESHOLD"]
        )

        risk_ceiling = float(
            self.thresholds["RISK_CEILING"]
        )

        if (
            has_history
            and trust > auto_threshold
            and risk < risk_ceiling
        ):
            decision = "AUTO"

        elif trust > propose_threshold:
            decision = "PROPOSE"

        else:
            decision = "ESCALATE"

        return GateResult(
            decision=decision,
            reversibility=reversibility,
            blast_radius=blast_radius,
            evidence_lower_bound=evidence_lower_bound,
            trust=trust,
            risk=risk,
            has_history=has_history,
        )