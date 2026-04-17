from __future__ import annotations

from app.domain.models import ConsistencyCheckResult, LLMAnalysisResult, RiskScoreResult


def check_recommendation_consistency(
    risk: RiskScoreResult,
    analysis: LLMAnalysisResult,
) -> ConsistencyCheckResult:
    risk_band = risk.risk_band.lower().strip()
    recommendation = analysis.recommendation.lower().strip()

    if risk_band == "high" and recommendation == "go":
        return ConsistencyCheckResult(
            is_consistent=False,
            severity="critical",
            message="High-risk decision received GO recommendation.",
        )

    if risk_band == "low" and recommendation == "stop":
        return ConsistencyCheckResult(
            is_consistent=False,
            severity="critical",
            message="Low-risk decision received STOP recommendation.",
        )

    if risk_band == "medium" and recommendation in {"go", "stop"}:
        return ConsistencyCheckResult(
            is_consistent=False,
            severity="warning",
            message="Medium-risk decision received a strongly decisive recommendation.",
        )

    if recommendation == "needs_more_data":
        return ConsistencyCheckResult(
            is_consistent=True,
            severity="info",
            message="Recommendation requests more information before a final decision.",
        )

    return ConsistencyCheckResult(
        is_consistent=True,
        severity="none",
        message="Recommendation is consistent with risk band.",
    )