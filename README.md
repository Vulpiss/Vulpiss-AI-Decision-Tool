# 🧠 AI-Based Decision Risk Evaluation Tool

**Decision Support System for Risk Evaluation, Recommendation and Explainability**

---

## 📌 Overview

This project is a **decision support application** designed to help evaluate complex decisions under uncertainty.

The system combines:

* deterministic **risk scoring**
* rule-based **decision policy**
* AI-powered **explainability (LLM)**
* structured **reporting**
* persistent **decision history**

It is delivered as a **standalone desktop application (.exe)**.

---

## 🖥️ Application Preview

*(Add screenshot here — GUI window)*

---

## ⚙️ Core Features

### 🔹 Risk Scoring Engine

* Score: **0–100**
* Risk bands: `LOW / MEDIUM / HIGH`
* Deterministic and explainable

---

### 🔹 Score Breakdown

Each decision is evaluated based on:

* uncertainty
* knowledge gap
* reversibility
* time horizon
* financial exposure

---

### 🔹 Decision Policy Layer

Outputs:

* `GO`
* `PIVOT`
* `STOP`
* `NEEDS_MORE_DATA`

👉 Fully rule-based and auditable

---

### 🔹 AI Explainability (LLM)

Generates:

* summary
* risk factors
* upside factors
* scenarios (best / base / worst)
* mitigations
* missing information
* red flags

👉 AI explains decisions — **it does not make them**

---

### 🔹 GUI Application

User can:

* input decision data
* run analysis
* view results instantly
* load/save decisions
* export reports
* browse decision history

---

### 🔹 Decision History

* stored in SQLite database
* last decisions visible in GUI
* one-click reload into form

---

### 🔹 Reporting

* full decision report generated
* saved as `.txt`
* exportable via GUI

---

### 🔹 Standalone EXE

* no Python required
* double-click to run
* fully local execution

---

## 🧱 System Architecture

```id="arch1"
Input → Risk Engine → Policy → LLM → Consistency Check → Report → Database → GUI
```

---

## 🚀 How to Run

### Option 1 — EXE (Recommended)

```id="runexe"
dist/DecisionTool.exe
```

---

### Option 2 — Python

```bash id="runpy"
python -m app.gui.gui_app
```

---

## 📊 Example Output

```id="output1"
Risk Score: 45/100
Risk Band: MEDIUM
Recommendation: PIVOT
```

---

## 🧠 Design Principles

* Separation of concerns (risk ≠ decision ≠ explanation)
* Deterministic core logic
* AI used only for interpretation
* Explainability-first approach
* Product-oriented architecture

---

## ⚠️ Limitations

* synthetic dataset
* rule-based policy
* no real-world calibration yet

---

## 🔮 Future Improvements

* ML-based risk model
* model vs rule comparison
* web interface (FastAPI)
* PDF reports
* advanced analytics dashboard

---

## 🎯 Project Goal

Demonstrate:

* system design for decision-making tools
* practical use of AI in controlled environments
* explainable decision pipelines
* product-oriented AI development

---

## 📎 Author

AI & Data Solutions Developer (in transition)

---
