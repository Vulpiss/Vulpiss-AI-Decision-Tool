from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.domain.models import DecisionInput, LLMAnalysisResult, RiskScoreResult


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,

            decision_title TEXT,
            decision_type TEXT,

            cost REAL,
            expected_upside REAL,
            time_horizon_months INTEGER,

            uncertainty_level INTEGER,
            knowledge_level INTEGER,
            reversible INTEGER,
            notes TEXT,

            risk_score INTEGER,
            risk_band TEXT,

            recommendation TEXT,
            confidence INTEGER
        )
    """)

    conn.commit()
    conn.close()


def save_log(
    decision: DecisionInput,
    risk: RiskScoreResult,
    analysis: LLMAnalysisResult,
    db_path: str,
) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO decisions (
            timestamp,
            decision_title,
            decision_type,
            cost,
            expected_upside,
            time_horizon_months,
            uncertainty_level,
            knowledge_level,
            reversible,
            notes,
            risk_score,
            risk_band,
            recommendation,
            confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        decision.decision_title,
        decision.decision_type,
        decision.cost,
        decision.expected_upside,
        decision.time_horizon_months,
        decision.uncertainty_level,
        decision.knowledge_level,
        int(decision.reversible),
        decision.notes,
        risk.risk_score,
        risk.risk_band,
        analysis.recommendation,
        analysis.confidence,
    ))

    conn.commit()
    conn.close()