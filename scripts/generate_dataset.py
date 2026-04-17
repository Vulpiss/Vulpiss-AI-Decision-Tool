from __future__ import annotations

import json
import random
from pathlib import Path


# 🔥 zmienione na v3 (żeby nie nadpisać starego)
OUTPUT_PATH = Path("data/decision_dataset_2500_v3.json")
DATASET_SIZE = 2500


DECISION_TYPES = [
    "capex_purchase",
    "product_launch",
    "business_expansion",
    "marketing_campaign",
    "technology_upgrade",
    "hiring_decision",
    "market_entry",
    "partnership",
]

DECISION_TITLES = [
    "Purchase new equipment",
    "Launch new product line",
    "Open second location",
    "Upgrade server infrastructure",
    "Expand marketing campaign",
    "Enter new regional market",
    "Hire senior engineer",
    "Invest in automation",
    "Upgrade production line",
    "Form strategic partnership",
]


def assign_label(
    cost: float,
    expected_upside: float,
    uncertainty_level: int,
    knowledge_level: int,
    reversible: bool,
    time_horizon_months: int,
) -> str:
    # STOP
    if (
        uncertainty_level >= 4
        and knowledge_level <= 2
        and not reversible
        and cost >= expected_upside
    ):
        return "stop"

    if (
        uncertainty_level == 5
        and not reversible
        and time_horizon_months >= 18
    ):
        return "stop"

    if (
        cost > expected_upside * 1.2
        and knowledge_level <= 2
    ):
        return "stop"

    # GO
    if (
        uncertainty_level <= 2
        and knowledge_level >= 4
        and reversible
        and expected_upside >= cost * 1.5
        and time_horizon_months <= 18
    ):
        return "go"

    if (
        uncertainty_level == 1
        and knowledge_level >= 4
        and expected_upside > cost
    ):
        return "go"

    return "pivot"


def base_record(index, cost, expected_upside, uncertainty, knowledge, reversible, time_horizon):
    label = assign_label(
        cost,
        expected_upside,
        uncertainty,
        knowledge,
        reversible,
        time_horizon,
    )

    return {
        "decision_title": f"{random.choice(DECISION_TITLES)} #{index + 1}",
        "decision_type": random.choice(DECISION_TYPES),
        "time_horizon_months": time_horizon,
        "cost": cost,
        "expected_upside": expected_upside,
        "uncertainty_level": uncertainty,
        "knowledge_level": knowledge,
        "reversible": reversible,
        "notes": "Balanced dataset entry.",
        "label": label,
    }


# 🟢 GO — realistyczne (nie stałe wartości)
def generate_go_record(index: int) -> dict:
    cost = random.randint(2_000, 50_000)
    expected_upside = random.randint(int(cost * 1.5), int(cost * 4))
    uncertainty = random.randint(1, 2)
    knowledge = random.randint(4, 5)
    reversible = random.choice([True, True, True, False])  # bias na True
    time_horizon = random.randint(3, 12)

    return base_record(index, cost, expected_upside, uncertainty, knowledge, reversible, time_horizon)


# 🔴 STOP — realistyczne
def generate_stop_record(index: int) -> dict:
    cost = random.randint(50_000, 200_000)
    expected_upside = random.randint(1_000, int(cost * 0.9))
    uncertainty = random.randint(4, 5)
    knowledge = random.randint(1, 2)
    reversible = random.choice([False, False, False, True])  # bias na False
    time_horizon = random.randint(18, 36)

    return base_record(index, cost, expected_upside, uncertainty, knowledge, reversible, time_horizon)


# 🟡 PIVOT — środek
def generate_pivot_record(index: int) -> dict:
    cost = random.randint(10_000, 100_000)
    expected_upside = random.randint(int(cost * 0.8), int(cost * 1.5))
    uncertainty = random.randint(2, 4)
    knowledge = random.randint(2, 4)
    reversible = random.choice([True, False])
    time_horizon = random.randint(6, 24)

    return base_record(index, cost, expected_upside, uncertainty, knowledge, reversible, time_horizon)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dataset = []

    # ~1/3 GO
    for i in range(800):
        dataset.append(generate_go_record(i))

    # ~1/3 PIVOT
    for i in range(800, 1600):
        dataset.append(generate_pivot_record(i))

    # ~1/3 STOP
    for i in range(1600, DATASET_SIZE):
        dataset.append(generate_stop_record(i))

    random.shuffle(dataset)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    label_counts = {"go": 0, "pivot": 0, "stop": 0}
    for row in dataset:
        label_counts[row["label"]] += 1

    print("Dataset generated successfully.")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Dataset size: {len(dataset)}")
    print("Label distribution:")
    for label, count in label_counts.items():
        print(f"- {label.upper()}: {count}")


if __name__ == "__main__":
    main()