from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class DecisionInput:
    decision_title: str
    decision_type: str
    time_horizon_months: int
    cost: float
    expected_upside: float
    uncertainty_level: int
    knowledge_level: int
    reversible: bool
    notes: str = ""

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskScoreResult:
    risk_score: int
    risk_band: str
    scoring_notes: List[str]
    score_breakdown: Dict[str, int]

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LLMAnalysisResult:
    summary: str
    risk_factors: List[str]
    upside_factors: List[str]
    scenarios: Dict[str, str]
    recommendation: str
    confidence: int
    mitigations: List[str]
    missing_information: List[str]
    red_flags: List[str]
    policy_notes: List[str]

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyCheckResult:
    is_consistent: bool
    severity: str
    message: str

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)