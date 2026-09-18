from dataclasses import dataclass
from scipy.stats import beta as beta_distribution


@dataclass
class BetaEvidence:
    """
    Tracks evidence for one action in one machine class.

    Starts with a Beta(1, 1) prior.
    """

    alpha: int = 1
    beta: int = 1

    def record_success(self):
        """Record a successful remediation."""
        self.alpha += 1

    def record_failure(self):
        """Record a failed remediation."""
        self.beta += 1

    @property
    def mean(self):
        """Return the posterior mean."""
        return self.alpha / (self.alpha + self.beta)

    def lower_bound(self, percentile=0.05):
        """
        Return a conservative lower percentile
        of the Beta posterior.
        """
        return beta_distribution.ppf(
            percentile,
            self.alpha,
            self.beta,
        )


class EvidenceStore:
    """
    Stores evidence separately for each
    (action_type, machine_class) combination.
    """

    def __init__(self):
        self._evidence = {}

    def get(self, action_type, machine_class):
        """
        Get the evidence tracker for an action
        and machine class.

        New combinations start with Beta(1, 1).
        """
        key = (action_type, machine_class)

        if key not in self._evidence:
            self._evidence[key] = BetaEvidence()

        return self._evidence[key]

    def record_success(self, action_type, machine_class):
        """Record a successful action."""
        evidence = self.get(action_type, machine_class)
        evidence.record_success()

    def record_failure(self, action_type, machine_class):
        """Record a failed action."""
        evidence = self.get(action_type, machine_class)
        evidence.record_failure()

    def get_lower_bound(
        self,
        action_type,
        machine_class,
        percentile=0.05,
    ):
        """Return the conservative evidence score."""
        evidence = self.get(action_type, machine_class)

        return evidence.lower_bound(percentile)