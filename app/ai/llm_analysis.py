from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.domain.models import DecisionInput, LLMAnalysisResult, RiskScoreResult


VALID_RECOMMENDATIONS = {"go", "pivot", "stop", "needs_more_data"}
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise NotImplementedError("OPENAI_API_KEY is not set.")
        _client = OpenAI(api_key=api_key)

    return _client


def build_prompt(
    decision: DecisionInput,
    risk: RiskScoreResult,
    recommendation: str,
    confidence: int,
    policy_notes: List[str],
) -> str:
    input_json = json.dumps(decision.to_json(), ensure_ascii=False, indent=2)
    scoring_notes = "; ".join(risk.scoring_notes)
    policy_notes_text = "; ".join(policy_notes) if policy_notes else "No additional policy notes."

    return f"""
Task: Explain a decision using structured inputs, a precomputed risk score, and a precomputed recommendation.

CONTEXT
- Decision title: {decision.decision_title}
- Decision type: {decision.decision_type}
- Time horizon (months): {decision.time_horizon_months}

INPUT DATA (structured)
{input_json}

RISK SCORING (computed outside the LLM)
- risk_score: {risk.risk_score}
- risk_band: {risk.risk_band}
- scoring_notes: {scoring_notes}

DECISION POLICY (computed outside the LLM)
- recommendation: {recommendation}
- confidence: {confidence}
- policy_notes: {policy_notes_text}

RULES
1) Do NOT recalculate the risk score.
2) Do NOT replace the recommendation with a different one.
3) You are explaining the decision, not making the core decision.
4) If something is unknown, include it in `missing_information`.
5) Use concise, business-oriented language.
6) Return ONLY valid JSON matching this schema:

{{
  "summary": "string",
  "risk_factors": ["string", "..."],
  "upside_factors": ["string", "..."],
  "scenarios": {{
    "best_case": "string",
    "base_case": "string",
    "worst_case": "string"
  }},
  "recommendation": "go|pivot|stop|needs_more_data",
  "confidence": 1,
  "mitigations": ["string", "..."],
  "missing_information": ["string", "..."],
  "red_flags": ["string", "..."]
}}

Return the same recommendation and confidence as provided above.
""".strip()


def call_llm(prompt: str) -> str:
    client = get_client()

    response = client.responses.create(
        model=MODEL_NAME,
        instructions="You are a careful AI analyst. Return only valid JSON.",
        input=prompt,
    )

    return response.output_text


def parse_llm_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM output is not valid JSON: {exc}") from exc


def _validate_string_list(name: str, value: Any) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list.")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must contain only strings.")


def validate_analysis(data: Dict[str, Any]) -> None:
    required_keys = {
        "summary",
        "risk_factors",
        "upside_factors",
        "scenarios",
        "recommendation",
        "confidence",
        "mitigations",
        "missing_information",
        "red_flags",
    }

    missing = required_keys.difference(data.keys())
    if missing:
        raise ValueError(f"Missing keys in LLM output: {sorted(missing)}")

    if not isinstance(data["summary"], str) or not data["summary"].strip():
        raise ValueError("summary must be a non-empty string.")

    _validate_string_list("risk_factors", data["risk_factors"])
    _validate_string_list("upside_factors", data["upside_factors"])
    _validate_string_list("mitigations", data["mitigations"])
    _validate_string_list("missing_information", data["missing_information"])
    _validate_string_list("red_flags", data["red_flags"])

    recommendation = str(data["recommendation"]).lower().strip()
    if recommendation not in VALID_RECOMMENDATIONS:
        raise ValueError("Invalid recommendation value.")

    try:
        parsed_confidence = int(data["confidence"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Confidence must be an integer.") from exc

    if not (1 <= parsed_confidence <= 5):
        raise ValueError("Confidence must be between 1 and 5.")

    scenarios = data["scenarios"]
    if not isinstance(scenarios, dict):
        raise ValueError("scenarios must be an object.")

    for key in ("best_case", "base_case", "worst_case"):
        if key not in scenarios:
            raise ValueError(f"Missing scenario: {key}")
        if not isinstance(scenarios[key], str) or not scenarios[key].strip():
            raise ValueError(f"Scenario '{key}' must be a non-empty string.")


def _normalize_parsed_output(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(data)
    normalized["recommendation"] = str(normalized["recommendation"]).lower().strip()
    normalized["confidence"] = int(normalized["confidence"])
    return normalized


def _fallback_analysis(
    decision: DecisionInput,
    risk: RiskScoreResult,
    recommendation: str,
    confidence: int,
    policy_notes: List[str],
) -> LLMAnalysisResult:
    risk_factors = list(risk.scoring_notes)
    upside_factors: List[str] = []
    mitigations: List[str] = []
    missing_information: List[str] = []
    red_flags: List[str] = []

    if decision.expected_upside > decision.cost:
        upside_factors.append("Expected upside is higher than upfront cost.")
    if decision.reversible:
        upside_factors.append("The decision is reversible, reducing long-term downside.")
    if decision.knowledge_level >= 4:
        upside_factors.append("Knowledge level is strong enough to support execution.")
    if decision.uncertainty_level >= 4:
        red_flags.append("High uncertainty increases the chance of a wrong call.")
    if decision.knowledge_level <= 2:
        missing_information.append("Decision assumptions need stronger evidence or validation.")
    if decision.time_horizon_months > 18:
        red_flags.append("Long time horizon may invalidate current assumptions.")

    mitigations.extend(
        [
            "Validate the core assumptions before committing full budget.",
            "Break the decision into stages with review checkpoints.",
        ]
    )
    if not decision.reversible:
        mitigations.append("Define a stop-loss or exit trigger before execution.")

    summary = (
        f"This is a {risk.risk_band}-risk decision with a score of {risk.risk_score}/100. "
        f"Recommended action is {recommendation.upper()}. "
        f"Main drivers: {'; '.join(risk.scoring_notes)}"
    )

    return LLMAnalysisResult(
        summary=summary,
        risk_factors=risk_factors or ["No dominant risk factor was explicitly identified."],
        upside_factors=upside_factors or ["No strong upside signal was detected beyond the stated expected upside."],
        scenarios={
            "best_case": "Execution is disciplined, assumptions hold, and the upside is realized on schedule.",
            "base_case": "The decision performs close to expectations, but requires active monitoring and mitigation.",
            "worst_case": "Key assumptions fail, cost is sunk, and recovery options are limited.",
        },
        recommendation=recommendation,
        confidence=confidence,
        mitigations=mitigations,
        missing_information=missing_information,
        red_flags=red_flags,
        policy_notes=policy_notes,
    )


def run_llm_analysis(
    decision: DecisionInput,
    risk: RiskScoreResult,
    recommendation: str,
    confidence: int,
    policy_notes: List[str],
) -> LLMAnalysisResult:
    prompt = build_prompt(
        decision=decision,
        risk=risk,
        recommendation=recommendation,
        confidence=confidence,
        policy_notes=policy_notes,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_text = call_llm(prompt)
            parsed = parse_llm_json(raw_text)
            validate_analysis(parsed)
            parsed = _normalize_parsed_output(parsed)

            if parsed["recommendation"] != recommendation:
                raise ValueError(
                    f"LLM changed recommendation from '{recommendation}' to '{parsed['recommendation']}'."
                )

            if parsed["confidence"] != confidence:
                raise ValueError(
                    f"LLM changed confidence from '{confidence}' to '{parsed['confidence']}'."
                )

            return LLMAnalysisResult(
                summary=parsed["summary"],
                risk_factors=parsed["risk_factors"],
                upside_factors=parsed["upside_factors"],
                scenarios=parsed["scenarios"],
                recommendation=parsed["recommendation"],
                confidence=parsed["confidence"],
                mitigations=parsed["mitigations"],
                missing_information=parsed["missing_information"],
                red_flags=parsed["red_flags"],
                policy_notes=policy_notes,
            )
        except Exception as exc:
            if attempt >= MAX_RETRIES:
                print(f"[WARN] LLM analysis failed after {attempt} attempts. Using fallback. Error: {exc}")
                return _fallback_analysis(
                    decision=decision,
                    risk=risk,
                    recommendation=recommendation,
                    confidence=confidence,
                    policy_notes=policy_notes,
                )

            print(f"[WARN] LLM attempt {attempt} failed: {exc}. Retrying...")
            time.sleep(RETRY_DELAY_SECONDS)

    return _fallback_analysis(
        decision=decision,
        risk=risk,
        recommendation=recommendation,
        confidence=confidence,
        policy_notes=policy_notes,
    )