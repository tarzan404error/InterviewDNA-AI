Build a complete production-ready AI-Powered Mock Interview Platform called "InterviewDNA AI".

IMPORTANT:
This is NOT a chatbot project.

The system must simulate a real interview process using state management, adaptive decision making, dynamic difficulty adjustment, scoring logic, interview termination rules, and explainable candidate evaluation.

The application should be highly polished, unique, visually appealing, and suitable for winning a hackathon.

TECH STACK:

* Python
* Streamlit
* Gemini API
* Pandas
* Plotly
* JSON-based storage

GOAL:

Create an intelligent interview simulation platform that evaluates candidates based on:

1. Resume
2. Job Description
3. Technical knowledge
4. Communication quality
5. Adaptability
6. Time management
7. Consistency
8. Performance under pressure

UNIQUE DIFFERENTIATOR:

Instead of generating only a final score, build a dynamic Interview DNA Engine.

The Interview DNA Engine must continuously calculate:

* Knowledge Index
* Communication Index
* Adaptability Index
* Confidence Index
* Consistency Index
* Pressure Handling Index

At the end of the interview, generate a complete Interview DNA Profile.

=========================================
FEATURE 1: RESUME ANALYZER
==========================

Allow upload of PDF Resume.

Extract:

* Skills
* Projects
* Experience
* Education

Generate:

* Candidate Profile
* Skill Inventory
* Role Alignment Score

=========================================
FEATURE 2: JOB DESCRIPTION ANALYZER
===================================

Allow upload or paste JD.

Extract:

* Required Skills
* Responsibilities
* Experience Level
* Keywords

Generate:

* Skill Match %
* Missing Skills
* Role Fit Analysis

=========================================
FEATURE 3: AI INTERVIEW ENGINE
==============================

Question Categories:

* Technical
* Conceptual
* Behavioural
* Scenario Based

Difficulty Levels:

Easy
Medium
Hard

Initial difficulty should depend on Resume-JD match.

Rules:

If candidate performs strongly:
Increase difficulty.

If candidate performs poorly:
Decrease difficulty.

Maintain complete interview state.

=========================================
FEATURE 4: INTERVIEW STATE MACHINE
==================================

Track:

Current Question
Current Difficulty
Total Score
Consecutive Failures
Response Time
Interview Status

Create a robust state manager.

=========================================
FEATURE 5: RESPONSE TIMER
=========================

Every question must have a timer.

Calculate:

Time Efficiency Score

Penalize:

* Very late answers
* Empty answers
* Extremely short answers

=========================================
FEATURE 6: ANSWER EVALUATION
============================

Evaluate every answer on:

Accuracy
Clarity
Depth
Relevance

Return scores from 0-100.

Generate short explanation for each score.

=========================================
FEATURE 7: PRESSURE MODE
========================

UNIQUE FEATURE

After a few successful answers:

Activate Pressure Mode.

Pressure Mode should:

* Reduce answer time
* Increase question difficulty
* Ask scenario-based questions

Evaluate how performance changes under pressure.

Generate Pressure Handling Score.

=========================================
FEATURE 8: ADAPTABILITY ENGINE
==============================

Measure:

How quickly candidate recovers after weak answers.

Generate Adaptability Index.

Example:

Weak answer
→ Next answer excellent

Adaptability increases.

=========================================
FEATURE 9: CONSISTENCY ENGINE
=============================

Measure variance between answers.

Stable performance:
High consistency.

Unstable performance:
Lower consistency.

=========================================
FEATURE 10: EARLY TERMINATION
=============================

Terminate interview when:

* Multiple consecutive failures
* Extremely poor performance
* Multiple unanswered questions

Show reason.

=========================================
FEATURE 11: INTERVIEW DNA REPORT
================================

Generate:

Final Readiness Score

Knowledge Index
Communication Index
Adaptability Index
Confidence Index
Consistency Index
Pressure Handling Index

Strengths
Weaknesses
Improvement Areas

Hiring Recommendation:

* Strongly Recommended
* Recommended
* Needs Improvement

=========================================
FEATURE 12: VISUAL DASHBOARD
============================

Create beautiful charts using Plotly.

Include:

1. Radar Chart
2. Skill Breakdown
3. Difficulty Timeline
4. Score Timeline
5. Interview DNA Visualization

=========================================
FEATURE 13: INTERVIEW TIMELINE
==============================

Display:

Question Number
Difficulty
Time Taken
Score

Example:

Q1 Easy 85
Q2 Easy 90
Difficulty Increased
Q3 Medium 80

Show every state transition.

=========================================
FEATURE 14: EXPLAINABLE AI
==========================

For every recommendation:

Show WHY.

For every score:

Show reasoning.

The evaluator should be transparent.

=========================================
UI REQUIREMENTS
===============

Modern dark theme.

Professional hiring platform feel.

Responsive layout.

Hackathon winning appearance.

=========================================
DELIVERABLES
============

Generate:

1. Complete project architecture
2. Folder structure
3. Full code
4. Streamlit UI
5. Gemini integration
6. Requirements.txt
7. README.md
8. Setup instructions
9. Deployment guide

The code must be modular, scalable, clean, documented, and ready for GitHub submission.
