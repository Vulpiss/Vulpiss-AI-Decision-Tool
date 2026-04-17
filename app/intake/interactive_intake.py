from __future__ import annotations

from typing import Optional

from app.domain.models import DecisionInput


def _ask_non_empty_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("[WARN] This field cannot be empty.")


def _ask_int(
    prompt: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    while True:
        raw = input(prompt).strip()

        try:
            value = int(raw)
        except ValueError:
            print("[WARN] Please enter a valid integer.")
            continue

        if min_value is not None:
            min_limit = min_value
            if value < min_limit:
                print(f"[WARN] Value must be >= {min_limit}.")
                continue

        if max_value is not None:
            max_limit = max_value
            if value > max_limit:
                print(f"[WARN] Value must be <= {max_limit}.")
                continue

        return value


def _ask_float(
    prompt: str,
    min_value: Optional[float] = None,
) -> float:
    while True:
        raw = input(prompt).strip().replace(",", ".")

        try:
            value = float(raw)
        except ValueError:
            print("[WARN] Please enter a valid number.")
            continue

        if min_value is not None:
            min_limit = min_value
            if value < min_limit:
                print(f"[WARN] Value must be >= {min_limit}.")
                continue

        return value


def _ask_bool(prompt: str) -> bool:
    while True:
        raw = input(prompt).strip().lower()

        if raw in {"y", "yes", "t", "true", "1"}:
            return True
        if raw in {"n", "no", "f", "false", "0"}:
            return False

        print("[WARN] Please answer with y/n.")


def build_decision_interactively() -> DecisionInput:
    print("\nINTERACTIVE DECISION INTAKE")
    print("===========================")
    print("Fill in the decision context below.\n")

    decision_title = _ask_non_empty_text("Decision title: ")
    decision_type = _ask_non_empty_text("Decision type: ")
    time_horizon_months = _ask_int("Time horizon (months): ", min_value=0)
    cost = _ask_float("Cost: ", min_value=0.0)
    expected_upside = _ask_float("Expected upside: ", min_value=0.0)
    uncertainty_level = _ask_int("Uncertainty level (1-5): ", min_value=1, max_value=5)
    knowledge_level = _ask_int("Knowledge level (1-5): ", min_value=1, max_value=5)
    reversible = _ask_bool("Is the decision reversible? (y/n): ")
    notes = input("Additional notes (optional): ").strip()

    decision = DecisionInput(
        decision_title=decision_title,
        decision_type=decision_type,
        time_horizon_months=time_horizon_months,
        cost=cost,
        expected_upside=expected_upside,
        uncertainty_level=uncertainty_level,
        knowledge_level=knowledge_level,
        reversible=reversible,
        notes=notes,
    )

    print("\n[INFO] Decision input created successfully.")
    print("[INFO] Review:")
    print(f"  - Title: {decision.decision_title}")
    print(f"  - Type: {decision.decision_type}")
    print(f"  - Time horizon: {decision.time_horizon_months} months")
    print(f"  - Cost: {decision.cost}")
    print(f"  - Expected upside: {decision.expected_upside}")
    print(f"  - Uncertainty: {decision.uncertainty_level}/5")
    print(f"  - Knowledge: {decision.knowledge_level}/5")
    print(f"  - Reversible: {decision.reversible}")
    print(f"  - Notes: {decision.notes if decision.notes else 'None'}")

    return decision