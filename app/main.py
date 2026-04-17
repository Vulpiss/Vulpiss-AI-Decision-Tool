from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from app.ai.llm_analysis import run_llm_analysis
from app.domain.consistency import check_recommendation_consistency
from app.domain.models import DecisionInput
from app.infrastructure.database import init_db, save_log
from app.intake.interactive_intake import build_decision_interactively
from app.policy.recommendation_policy import decide_recommendation
from app.reporting.report_generator import generate_report
from app.risk_engine.risk_scoring import calculate_risk


EXAMPLE_DECISION: Dict[str, Any] = {
    "decision_title": "Purchase new equipment",
    "decision_type": "capex_purchase",
    "time_horizon_months": 18,
    "cost": 12000,
    "expected_upside": 22000,
    "uncertainty_level": 2,
    "knowledge_level": 4,
    "reversible": True,
    "notes": "Equipment should improve throughput, but demand assumptions are not fully validated.",
}


def load_decision_from_json(file_path: str) -> DecisionInput:
    try:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        return DecisionInput(**data)
    except Exception as exc:
        raise ValueError(f"Invalid decision JSON: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI-Based Decision Risk Evaluation Tool")
    parser.add_argument("--input", help="Path to decision JSON input file.")
    parser.add_argument("--interactive", action="store_true", help="Run interactive decision form.")
    parser.add_argument("--db", default="decisions.db", help="SQLite database path.")
    parser.add_argument("--report", default="report.txt", help="Report output path.")
    parser.add_argument(
        "--print-example",
        action="store_true",
        help="Print example decision JSON and exit.",
    )
    return parser


def run(decision: DecisionInput, db_path: str, report_path: str) -> str:
    print("[INFO] Initializing system...")
    init_db(db_path)

    print("[INFO] Calculating risk...")
    risk = calculate_risk(decision)

    print("[INFO] Applying recommendation policy...")
    policy = decide_recommendation(decision, risk)

    print("[INFO] Running LLM analysis...")
    analysis = run_llm_analysis(
        decision=decision,
        risk=risk,
        recommendation=policy.recommendation,
        confidence=policy.confidence,
        policy_notes=policy.policy_notes,
    )

    print("[INFO] Checking consistency...")
    consistency = check_recommendation_consistency(risk, analysis)
    print(f"[CONSISTENCY] {consistency.severity.upper()} - {consistency.message}")

    print("[INFO] Generating report...")
    report = generate_report(
        decision=decision,
        risk=risk,
        analysis=analysis,
        consistency=consistency,
        output_path=report_path,
    )

    print("[INFO] Saving to database...")
    save_log(
        decision=decision,
        risk=risk,
        analysis=analysis,
        db_path=db_path,
    )

    print("[INFO] Done.")
    return report


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.print_example:
        print(json.dumps(EXAMPLE_DECISION, indent=2, ensure_ascii=False))
        return

    print(f"[INFO] Using database: {args.db}")
    print(f"[INFO] Report will be saved to: {args.report}")

    try:
        if args.interactive:
            decision = build_decision_interactively()
        elif args.input:
            decision = load_decision_from_json(args.input)
        else:
            decision = DecisionInput(**EXAMPLE_DECISION)
    except Exception as exc:
        print(f"[ERROR] Failed to load decision input: {exc}")
        sys.exit(1)

    try:
        report = run(
            decision=decision,
            db_path=args.db,
            report_path=args.report,
        )
        print("\n===== FINAL REPORT =====\n")
        print(report)
    except Exception as exc:
        print(f"[ERROR] Execution failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()