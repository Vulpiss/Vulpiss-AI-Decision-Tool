from __future__ import annotations

from pathlib import Path

from app.domain.consistency import ConsistencyCheckResult
from app.domain.models import DecisionInput, LLMAnalysisResult, RiskScoreResult


DEFAULT_REPORT_PATH = "report.txt"


def _format_bullet_list(items: list[str]) -> str:
    if not items:
        return "None"
    return "\n- ".join(items)


def _format_score_breakdown(breakdown: dict[str, int]) -> str:
    ordered_keys = [
        "uncertainty",
        "knowledge_gap",
        "reversibility",
        "time_horizon",
        "financial_exposure",
    ]

    lines: list[str] = []
    for key in ordered_keys:
        value = breakdown.get(key, 0)
        lines.append(f"{key}: {value}")

    return "\n- ".join(lines) if lines else "None"


def generate_report(
    decision: DecisionInput,
    risk: RiskScoreResult,
    analysis: LLMAnalysisResult,
    consistency: ConsistencyCheckResult,
    output_path: str = DEFAULT_REPORT_PATH,
) -> str:
    scoring_notes_section = _format_bullet_list(risk.scoring_notes)
    score_breakdown_section = _format_score_breakdown(risk.score_breakdown)
    policy_notes_section = _format_bullet_list(analysis.policy_notes)
    missing_information_section = _format_bullet_list(analysis.missing_information)
    red_flags_section = _format_bullet_list(analysis.red_flags)
    risk_factors_section = _format_bullet_list(analysis.risk_factors)
    upside_factors_section = _format_bullet_list(analysis.upside_factors)
    mitigations_section = _format_bullet_list(analysis.mitigations)

    report = f"""DECISION REPORT
===============

Decision: {decision.decision_title}
Type: {decision.decision_type}
Time Horizon: {decision.time_horizon_months} months
Cost: {decision.cost}
Expected Upside: {decision.expected_upside}
Reversible: {decision.reversible}

RISK OUTPUT
-----------
Risk Score: {risk.risk_score}/100
Risk Band: {risk.risk_band.upper()}

Score Breakdown:
- {score_breakdown_section}

Scoring Notes:
- {scoring_notes_section}

CONSISTENCY CHECK
-----------------
Consistent: {consistency.is_consistent}
Severity: {consistency.severity.upper()}
Message: {consistency.message}

ANALYSIS
--------
Summary: {analysis.summary}
Recommendation: {analysis.recommendation.upper()}
Confidence: {analysis.confidence}/5

Policy Notes:
- {policy_notes_section}

Risk Factors:
- {risk_factors_section}

Upside Factors:
- {upside_factors_section}

Scenarios:
- Best Case: {analysis.scenarios['best_case']}
- Base Case: {analysis.scenarios['base_case']}
- Worst Case: {analysis.scenarios['worst_case']}

Mitigations:
- {mitigations_section}

Missing Information:
- {missing_information_section}

Red Flags:
- {red_flags_section}
"""

    Path(output_path).write_text(report, encoding="utf-8")
    return report