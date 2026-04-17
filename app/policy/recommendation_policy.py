from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.domain.models import DecisionInput, RiskScoreResult


VALID_RECOMMENDATIONS = {"go", "pivot", "stop", "needs_more_data"}


@dataclass
class PolicyDecision:
    recommendation: str
    confidence: int
    policy_notes: List[str]

    def __post_init__(self) -> None:
        recommendation = self.recommendation.lower().strip()
        if recommendation not in VALID_RECOMMENDATIONS:
            raise ValueError(f"Invalid recommendation: {self.recommendation}")
        if not (1 <= int(self.confidence) <= 5):
            raise ValueError("confidence must be between 1 and 5")

        self.recommendation = recommendation
        self.confidence = int(self.confidence)


def decide_recommendation(
    decision: DecisionInput,
    risk: RiskScoreResult,
) -> PolicyDecision:
    """
    Deterministic business policy layer.

    This module decides what to do with the risk estimate.
    It is intentionally separate from:
    - risk scoring
    - LLM explanation
    """
    notes: List[str] = []

    low_knowledge = decision.knowledge_level <= 2
    high_uncertainty = decision.uncertainty_level >= 4
    irreversible = not decision.reversible
    upside_below_cost = decision.expected_upside < decision.cost
    upside_exceeds_cost = decision.expected_upside >= decision.cost
    long_horizon = decision.time_horizon_months > 18

    if low_knowledge and high_uncertainty:
        notes.append("Low knowledge combined with high uncertainty makes the decision under-informed.")
        return PolicyDecision(
            recommendation="needs_more_data",
            confidence=5,
            policy_notes=notes,
        )

    if risk.risk_band == "high":
        if irreversible and upside_below_cost:
            notes.append("High-risk, irreversible decision with weak financial asymmetry.")
            return PolicyDecision(
                recommendation="stop",
                confidence=5,
                policy_notes=notes,
            )

        if irreversible:
            notes.append("High-risk decision is hard to reverse, so full commitment is not justified.")
            return PolicyDecision(
                recommendation="stop",
                confidence=4,
                policy_notes=notes,
            )

        if upside_exceeds_cost:
            notes.append("High-risk decision may still be viable only with redesign, staging, or partial rollout.")
            return PolicyDecision(
                recommendation="pivot",
                confidence=4,
                policy_notes=notes,
            )

        notes.append("High-risk profile does not justify a clean GO decision.")
        return PolicyDecision(
            recommendation="stop",
            confidence=4,
            policy_notes=notes,
        )

    if risk.risk_band == "medium":
        if low_knowledge:
            notes.append("Medium risk with weak knowledge base suggests validation before commitment.")
            return PolicyDecision(
                recommendation="needs_more_data",
                confidence=4,
                policy_notes=notes,
            )

        if upside_below_cost:
            notes.append("Medium-risk decision has weak payoff profile and should be reworked.")
            return PolicyDecision(
                recommendation="pivot",
                confidence=4,
                policy_notes=notes,
            )

        if long_horizon and high_uncertainty:
            notes.append("Medium risk is amplified by a long horizon and unstable assumptions.")
            return PolicyDecision(
                recommendation="pivot",
                confidence=3,
                policy_notes=notes,
            )

        notes.append("Medium-risk decision may proceed only after scope reduction or staged execution.")
        return PolicyDecision(
            recommendation="pivot",
            confidence=3,
            policy_notes=notes,
        )

    # LOW RISK
    if low_knowledge and decision.uncertainty_level >= 3:
        notes.append("Risk is low on paper, but information quality is still not strong enough.")
        return PolicyDecision(
            recommendation="needs_more_data",
            confidence=3,
            policy_notes=notes,
        )

    if upside_exceeds_cost:
        notes.append("Low-risk decision with acceptable upside profile supports execution.")
        return PolicyDecision(
            recommendation="go",
            confidence=4,
            policy_notes=notes,
        )

    notes.append("Low risk alone is not enough when upside does not justify the cost.")
    return PolicyDecision(
        recommendation="pivot",
        confidence=3,
        policy_notes=notes,
    )