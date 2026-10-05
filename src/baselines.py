from dataclasses import dataclass
from typing import Callable

from .simulator import Incident


@dataclass(frozen=True)
class PolicyDecision:
    """Policy decision for one incident."""

    mode: str
    action_type: str | None
    human_involved: bool


def always_ask(action_for: Callable[[Incident], str], incident: Incident) -> PolicyDecision:
    """Require human handling/approval before every candidate action."""
    return PolicyDecision("HUMAN_APPROVAL", action_for(incident), True)


def always_act(action_for: Callable[[Incident], str], incident: Incident) -> PolicyDecision:
    """Execute every candidate action without pre-action human approval."""
    return PolicyDecision("AUTO", action_for(incident), False)
