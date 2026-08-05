# Voice-Assisted Workplace Incident Management System

A machine-learning-driven workplace incident management application that supports:

- Guided voice incident reporting
- Structured manual incident reporting
- Batch CSV and Excel incident processing
- Multi-task workplace incident classification
- Confidence-based Decision Tier routing
- Historical relationship validation
- PDF, CSV and Excel report exports
- Interactive safety analytics dashboard

## Classification Targets

- Nature of Injury
- Body Part
- Event or Exposure
- Source of Injury

## Decision Tiers

- Auto Fill
- Suggest Review
- Manual Review

## Application Entry Point

```bash
streamlit run app.py
```

## Model

The application uses a shared multi-task DeBERTa model with four classification heads.

The model file is managed using Git Large File Storage.

## Main Modules

```text
app.py
core/
voice/
batch/
reports/
dashboard/
pages/
config/
models/
tokenizer/
data/
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```
