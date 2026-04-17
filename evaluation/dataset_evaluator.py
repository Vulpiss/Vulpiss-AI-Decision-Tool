from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.domain.models import DecisionInput
from app.policy.recommendation_policy import decide_recommendation
from app.risk_engine.risk_scoring import calculate_risk


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "decision_dataset_2500_v3.json"

LABELS = ["go", "pivot", "stop", "needs_more_data"]


def load_dataset(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_confusion_matrix(labels: list[str]) -> dict[str, dict[str, int]]:
    return {
        actual: {pred: 0 for pred in labels}
        for actual in labels
    }


def print_confusion_matrix(matrix: dict[str, dict[str, int]], labels: list[str]) -> None:
    print("\nCONFUSION MATRIX")
    print("================")

    header = "actual \\ predicted".ljust(22)
    for label in labels:
        header += label.rjust(18)
    print(header)

    for actual in labels:
        row = actual.ljust(22)
        for pred in labels:
            row += str(matrix[actual][pred]).rjust(18)
        print(row)


def compute_precision_recall(
    matrix: dict[str, dict[str, int]],
    labels: list[str],
) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}

    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[actual][label] for actual in labels if actual != label)
        fn = sum(matrix[label][pred] for pred in labels if pred != label)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        metrics[label] = {
            "precision": precision,
            "recall": recall,
        }

    return metrics


def evaluate() -> None:
    data = load_dataset(DATASET_PATH)

    total = len(data)
    correct = 0

    prediction_counts = Counter()
    label_counts = Counter()
    correct_counts = Counter()

    matrix = build_confusion_matrix(LABELS)

    false_go_total = 0
    false_go_from_stop = 0

    for item in data:
        label = str(item["label"]).lower().strip()

        if label not in LABELS:
            print(f"[WARN] Unknown label skipped: {label}")
            continue

        decision_data = {k: v for k, v in item.items() if k != "label"}
        decision = DecisionInput(**decision_data)

        risk = calculate_risk(decision)
        policy = decide_recommendation(decision, risk)

        prediction = policy.recommendation.lower().strip()

        if prediction not in LABELS:
            print(f"[WARN] Unknown prediction skipped: {prediction}")
            continue

        prediction_counts[prediction] += 1
        label_counts[label] += 1
        matrix[label][prediction] += 1

        if prediction == label:
            correct += 1
            correct_counts[label] += 1

        if prediction == "go" and label != "go":
            false_go_total += 1

        if prediction == "go" and label == "stop":
            false_go_from_stop += 1

    accuracy = correct / total if total else 0.0
    metrics = compute_precision_recall(matrix, LABELS)

    print("\nDATASET EVALUATION")
    print("==================")
    print(f"Dataset path: {DATASET_PATH}")
    print(f"Dataset size: {total}")
    print(f"Overall accuracy: {accuracy:.2%}")

    print("\nBreakdown by label:")
    for label in LABELS:
        label_total = label_counts[label]
        label_correct = correct_counts[label]
        label_acc = (label_correct / label_total) if label_total else 0.0
        print(f"- {label.upper()}: {label_acc:.2%} ({label_correct}/{label_total})")

    print("\nPrediction distribution:")
    for pred in LABELS:
        print(f"- {pred.upper()}: {prediction_counts[pred]}")

    print_confusion_matrix(matrix, LABELS)

    print("\nPRECISION / RECALL")
    print("==================")
    for label in LABELS:
        print(
            f"- {label.upper()}: "
            f"precision={metrics[label]['precision']:.2%}, "
            f"recall={metrics[label]['recall']:.2%}"
        )

    print("\nRISKY ERROR METRICS")
    print("===================")
    print(f"False GO total (pred=GO, actual!=GO): {false_go_total}")
    print(f"False GO from STOP (pred=GO, actual=STOP): {false_go_from_stop}")


if __name__ == "__main__":
    evaluate()