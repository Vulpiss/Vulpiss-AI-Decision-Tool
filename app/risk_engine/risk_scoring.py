from __future__ import annotations

from typing import Dict, List

from app.domain.models import DecisionInput, RiskScoreResult


def _validate_input(decision: DecisionInput) -> None:
    if not (1 <= decision.uncertainty_level <= 5):
        raise ValueError("uncertainty_level must be between 1 and 5")

    if not (1 <= decision.knowledge_level <= 5):
        raise ValueError("knowledge_level must be between 1 and 5")

    if decision.time_horizon_months < 0:
        raise ValueError("time_horizon_months must be >= 0")

    if decision.cost < 0:
        raise ValueError("cost must be >= 0")

    if decision.expected_upside < 0:
        raise ValueError("expected_upside must be >= 0")


def _score_uncertainty(decision: DecisionInput) -> int:
    mapping = {
        1: 4,
        2: 8,
        3: 14,
        4: 20,
        5: 26,
    }
    return mapping[decision.uncertainty_level]


def _score_knowledge_gap(decision: DecisionInput) -> int:
    mapping = {
        1: 24,
        2: 18,
        3: 12,
        4: 6,
        5: 2,
    }
    return mapping[decision.knowledge_level]


def _score_reversibility(decision: DecisionInput) -> int:
    return 4 if decision.reversible else 18


def _score_time_horizon(decision: DecisionInput) -> int:
    months = decision.time_horizon_months

    if months <= 3:
        return 3
    if months <= 6:
        return 6
    if months <= 12:
        return 10
    if months <= 24:
        return 15
    return 20


def _score_financial_exposure(decision: DecisionInput) -> int:
    if decision.expected_upside <= 0:
        return 22

    ratio = decision.cost / decision.expected_upside

    if ratio <= 0.25:
        return 4
    if ratio <= 0.50:
        return 8
    if ratio <= 0.75:
        return 12
    if ratio <= 1.00:
        return 18
    return 24


def _derive_risk_band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def calculate_risk(decision: DecisionInput) -> RiskScoreResult:
    _validate_input(decision)

    breakdown: Dict[str, int] = {
        "uncertainty": _score_uncertainty(decision),
        "knowledge_gap": _score_knowledge_gap(decision),
        "reversibility": _score_reversibility(decision),
        "time_horizon": _score_time_horizon(decision),
        "financial_exposure": _score_financial_exposure(decision),
    }

    risk_score = sum(breakdown.values())
    risk_score = max(0, min(100, risk_score))
    risk_band = _derive_risk_band(risk_score)

    scoring_notes: List[str] = []

    if breakdown["uncertainty"] >= 20:
        scoring_notes.append("Uncertainty is a major risk driver.")
    elif breakdown["uncertainty"] >= 14:
        scoring_notes.append("Uncertainty is materially increasing risk.")

    if breakdown["knowledge_gap"] >= 18:
        scoring_notes.append("Low knowledge level creates a significant decision-quality gap.")
    elif breakdown["knowledge_gap"] >= 12:
        scoring_notes.append("Knowledge gaps are still meaningful and should be reduced.")

    if breakdown["reversibility"] >= 18:
        scoring_notes.append("The decision is difficult to reverse, increasing downside exposure.")
    else:
        scoring_notes.append("The decision is reversible, which limits long-term downside.")

    if breakdown["time_horizon"] >= 15:
        scoring_notes.append("Long time horizon increases the chance that assumptions will drift.")
    elif breakdown["time_horizon"] >= 10:
        scoring_notes.append("Medium-to-long time horizon adds moderate execution uncertainty.")

    if breakdown["financial_exposure"] >= 18:
        scoring_notes.append("Financial exposure is high relative to expected upside.")
    elif breakdown["financial_exposure"] >= 12:
        scoring_notes.append("Financial exposure is non-trivial relative to upside.")
    else:
        scoring_notes.append("Financial exposure is acceptable relative to upside.")

    return RiskScoreResult(
        risk_score=risk_score,
        risk_band=risk_band,
        scoring_notes=scoring_notes,
        score_breakdown=breakdown,
    )