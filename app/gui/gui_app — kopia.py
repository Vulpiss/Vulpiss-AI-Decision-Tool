from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, scrolledtext

from app.ai.llm_analysis import run_llm_analysis
from app.domain.consistency import check_recommendation_consistency
from app.domain.models import DecisionInput
from app.infrastructure.database import init_db, save_log
from app.policy.recommendation_policy import decide_recommendation
from app.reporting.report_generator import generate_report
from app.risk_engine.risk_scoring import calculate_risk


DB_PATH = "decisions.db"
REPORT_PATH = "report.txt"


class DecisionToolGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AI Decision Risk Evaluation Tool")
        self.root.geometry("900x760")

        init_db(DB_PATH)

        self._build_form()

    def _build_form(self) -> None:
        main_frame = tk.Frame(self.root, padx=12, pady=12)
        main_frame.pack(fill="both", expand=True)

        title_label = tk.Label(
            main_frame,
            text="AI-Based Decision Risk Evaluation Tool",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(anchor="w", pady=(0, 10))

        form_frame = tk.Frame(main_frame)
        form_frame.pack(fill="x", pady=(0, 10))

        self.fields: dict[str, tk.Widget] = {}

        self._add_entry(form_frame, "Decision title:", "decision_title", 0)
        self._add_entry(form_frame, "Decision type:", "decision_type", 1)
        self._add_entry(form_frame, "Time horizon (months):", "time_horizon_months", 2)
        self._add_entry(form_frame, "Cost:", "cost", 3)
        self._add_entry(form_frame, "Expected upside:", "expected_upside", 4)
        self._add_entry(form_frame, "Uncertainty level (1-5):", "uncertainty_level", 5)
        self._add_entry(form_frame, "Knowledge level (1-5):", "knowledge_level", 6)

        reversible_label = tk.Label(form_frame, text="Is the decision reversible?")
        reversible_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=4)

        self.reversible_var = tk.BooleanVar(value=True)
        reversible_checkbox = tk.Checkbutton(form_frame, variable=self.reversible_var)
        reversible_checkbox.grid(row=7, column=1, sticky="w", pady=4)

        notes_label = tk.Label(form_frame, text="Additional notes:")
        notes_label.grid(row=8, column=0, sticky="nw", padx=(0, 10), pady=4)

        self.notes_text = tk.Text(form_frame, height=5, width=50)
        self.notes_text.grid(row=8, column=1, sticky="ew", pady=4)

        form_frame.columnconfigure(1, weight=1)

        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))

        analyze_button = tk.Button(
            button_frame,
            text="Analyze Decision",
            command=self.analyze_decision,
            width=20,
        )
        analyze_button.pack(side="left", padx=(0, 10))

        fill_example_button = tk.Button(
            button_frame,
            text="Load Example",
            command=self.load_example,
            width=20,
        )
        fill_example_button.pack(side="left")

        result_label = tk.Label(
            main_frame,
            text="Result",
            font=("Arial", 13, "bold"),
        )
        result_label.pack(anchor="w")

        self.result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=22)
        self.result_text.pack(fill="both", expand=True)

    def _add_entry(self, parent: tk.Frame, label_text: str, field_name: str, row: int) -> None:
        label = tk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)

        entry = tk.Entry(parent)
        entry.grid(row=row, column=1, sticky="ew", pady=4)

        self.fields[field_name] = entry

    def load_example(self) -> None:
        example = {
            "decision_title": "Purchase new equipment",
            "decision_type": "capex_purchase",
            "time_horizon_months": "18",
            "cost": "12000",
            "expected_upside": "22000",
            "uncertainty_level": "2",
            "knowledge_level": "4",
            "reversible": True,
            "notes": "Equipment should improve throughput, but demand assumptions are not fully validated.",
        }

        for field_name, value in example.items():
            if field_name == "reversible":
                self.reversible_var.set(bool(value))
            elif field_name == "notes":
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert(tk.END, str(value))
            else:
                entry = self.fields[field_name]
                if isinstance(entry, tk.Entry):
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "[INFO] Example data loaded.\n")

    def _build_decision_input(self) -> DecisionInput:
        try:
            decision = DecisionInput(
                decision_title=self._get_str("decision_title"),
                decision_type=self._get_str("decision_type"),
                time_horizon_months=self._get_int("time_horizon_months"),
                cost=self._get_float("cost"),
                expected_upside=self._get_float("expected_upside"),
                uncertainty_level=self._get_int("uncertainty_level"),
                knowledge_level=self._get_int("knowledge_level"),
                reversible=self.reversible_var.get(),
                notes=self.notes_text.get("1.0", tk.END).strip(),
            )
            return decision
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    def _get_str(self, field_name: str) -> str:
        widget = self.fields[field_name]
        if not isinstance(widget, tk.Entry):
            raise ValueError(f"Field '{field_name}' is not a text entry.")

        value = widget.get().strip()
        if not value:
            raise ValueError(f"Field '{field_name}' cannot be empty.")
        return value

    def _get_int(self, field_name: str) -> int:
        raw = self._get_str(field_name)
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"Field '{field_name}' must be an integer.") from exc

    def _get_float(self, field_name: str) -> float:
        raw = self._get_str(field_name).replace(",", ".")
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"Field '{field_name}' must be a number.") from exc

    def analyze_decision(self) -> None:
        self.result_text.delete("1.0", tk.END)

        try:
            decision = self._build_decision_input()

            risk = calculate_risk(decision)
            policy = decide_recommendation(decision, risk)

            analysis = run_llm_analysis(
                decision=decision,
                risk=risk,
                recommendation=policy.recommendation,
                confidence=policy.confidence,
                policy_notes=policy.policy_notes,
            )

            consistency = check_recommendation_consistency(risk, analysis)

            report = generate_report(
                decision=decision,
                risk=risk,
                analysis=analysis,
                consistency=consistency,
                output_path=REPORT_PATH,
            )

            save_log(
                decision=decision,
                risk=risk,
                analysis=analysis,
                db_path=DB_PATH,
            )

            output = (
                f"Decision: {decision.decision_title}\n"
                f"Type: {decision.decision_type}\n\n"
                f"Risk Score: {risk.risk_score}/100\n"
                f"Risk Band: {risk.risk_band.upper()}\n"
                f"Recommendation: {analysis.recommendation.upper()}\n"
                f"Confidence: {analysis.confidence}/5\n\n"
                f"Score Breakdown:\n"
                f"- uncertainty: {risk.score_breakdown.get('uncertainty', 0)}\n"
                f"- knowledge_gap: {risk.score_breakdown.get('knowledge_gap', 0)}\n"
                f"- reversibility: {risk.score_breakdown.get('reversibility', 0)}\n"
                f"- time_horizon: {risk.score_breakdown.get('time_horizon', 0)}\n"
                f"- financial_exposure: {risk.score_breakdown.get('financial_exposure', 0)}\n\n"
                f"Summary:\n{analysis.summary}\n\n"
                f"Consistency: {consistency.message}\n\n"
                f"Report saved to: {REPORT_PATH}\n"
                f"Database: {DB_PATH}\n"
            )

            self.result_text.insert(tk.END, output)

        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.result_text.insert(tk.END, f"[ERROR] {exc}\n")


def main() -> None:
    root = tk.Tk()
    app = DecisionToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()