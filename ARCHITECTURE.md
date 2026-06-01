# InterviewDNA AI Architecture

## Overview

InterviewDNA AI is organized into modular layers so the platform remains scalable, maintainable, and ready for production.

## Components

- `app.py`
  - Streamlit application entry point
  - User interface for resume analysis, JD analysis, interview execution, and reporting
  - Maintains session state and renders Plotly dashboards

- `core/`
  - `parser.py`: Resume and job description extraction logic
  - `questions.py`: Interview question library, difficulty selection, and adaptive difficulty rules
  - `evaluator.py`: Answer scoring heuristics and transparency explanations
  - `state_manager.py`: Interview state machine, history tracking, and termination rules
  - `analytics.py`: Interview DNA index calculations and final readiness report generation
  - `gemini_client.py`: Optional Gemini REST API client for AI-driven explanation enrichment
  - `interview_engine.py`: Orchestrator that connects parsing, question selection, answer evaluation, and report generation

- `utils/`
  - `storage.py`: JSON-based session and report persistence

- `storage/`
  - Holds exported interview reports and audit-ready JSON outputs

## Data Flow

1. Resume and JD inputs are parsed into structured candidate and role profiles.
2. The match engine computes a skill match score and initial difficulty.
3. The interview engine presents questions and captures answer time.
4. The evaluation engine scores each response on accuracy, clarity, depth, relevance, and time efficiency.
5. The state manager updates the interview state, applies consecutive failure and pressure mode rules, and decides whether to terminate.
6. Analytics compute Interview DNA indices and readiness recommendations.
7. The UI visualizes scores, timelines, and recommendations.

## Design Principles

- Modular: each core capability resides in its own Python module
- Explainable: every score is accompanied by reasoning
- Adaptive: difficulty changes dynamically based on candidate performance
- Pressure-aware: special mode triggers after strong answers to test resilience
- Persisted: output reports are saved in JSON format for traceability
- Presentable: dark-themed Streamlit UI with modern charts and polished layout

## Deployment

- `streamlit run app.py`
- Optional Gemini integration via environment variables
- JSON reports are exported to `storage/`
