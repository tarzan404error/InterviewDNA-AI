from typing import Dict, List
from core.questions import select_next_question, adjust_difficulty
from core.state_manager import InterviewState, QuestionHistory
from core.evaluator import evaluate_answer, explain_score
from core.analytics import calculate_dna_profile
from core.parser import parse_resume_text, parse_job_description
from core.fake_detector import detect_fake_resume, detect_fake_job_description


class InterviewCoordinator:
    def __init__(self):
        self.state = InterviewState()
        self.resume_profile = {}
        self.job_profile = {}
        self.skill_match = 0.0
        self.resume_integrity = {}
        self.jd_integrity = {}

    def analyze_resume(self, text: str) -> Dict[str, any]:
        self.resume_profile = parse_resume_text(text)
        self.resume_integrity = detect_fake_resume(text)
        return {**self.resume_profile, "integrity_check": self.resume_integrity}

    def analyze_job_description(self, text: str) -> Dict[str, any]:
        self.job_profile = parse_job_description(text)
        self.jd_integrity = detect_fake_job_description(text)
        return {**self.job_profile, "integrity_check": self.jd_integrity}

    def compute_match(self) -> float:
        resume_skills = set([skill.lower() for skill in self.resume_profile.get("skills", [])])
        jd_skills = set([skill.lower() for skill in self.job_profile.get("required_skills", [])])
        if not jd_skills:
            return 0.0
        matched = resume_skills.intersection(jd_skills)
        score = len(matched) / len(jd_skills) * 100.0
        self.skill_match = round(score, 1)
        return self.skill_match

    def role_alignment_score(self) -> float:
        if not self.job_profile:
            return 0.0
        base = self.compute_match()
        level_bonus = 5.0 if self.job_profile.get("experience_level", "Mid") == "Senior" else 3.0
        return min(100.0, base + level_bonus)

    def initial_difficulty(self) -> str:
        match = self.compute_match()
        if match >= 75:
            return "Medium"
        if match >= 45:
            return "Easy"
        return "Easy"

    def start_interview(self) -> Dict[str, any]:
        difficulty = self.initial_difficulty()
        self.state.begin(difficulty, self.skill_match)
        return {"status": self.state.status, "difficulty": difficulty}

    def next_question(self) -> Dict[str, any]:
        question = select_next_question(
            used_questions=[entry.question_id for entry in self.state.question_history],
            difficulty=self.state.current_difficulty,
            pressure_mode=self.state.pressure_mode,
            resume_profile=self.resume_profile,
            job_profile=self.job_profile,
        )
        if question is None:
            self.state.status = "finished"
            return {}
        self.state.record_question(question)
        return question

    def answer_question(self, answer: str, time_taken: float) -> Dict[str, any]:
        question = self.state.current_question
        if not question:
            return {}
        evaluation = evaluate_answer(
            answer=answer,
            topics=question.get("topics", []),
            difficulty=question.get("difficulty", "Easy"),
            time_taken=time_taken,
            is_pressure=self.state.pressure_mode,
            question_text=question.get("text", "")
        )
        explanation = explain_score(answer, evaluation)
        history = QuestionHistory(
            question_id=question["id"],
            category=question["category"],
            difficulty=question["difficulty"],
            text=question["text"],
            score=evaluation["score"],
            accuracy=evaluation["accuracy"],
            clarity=evaluation["clarity"],
            depth=evaluation["depth"],
            relevance=evaluation["relevance"],
            time_taken=time_taken,
            is_pressure=self.state.pressure_mode,
            answer=answer,
            explanation=explanation,
            is_plagiarism_suspicious=evaluation.get("is_plagiarism_suspicious", False),
            is_time_anomaly_suspicious=evaluation.get("is_time_anomaly_suspicious", False),
            plagiarism_risk=evaluation.get("plagiarism_risk", 0.0),
            time_anomaly_risk=evaluation.get("time_anomaly_risk", 0.0),
        )
        self.state.record_answer(history)
        self.state.current_difficulty = adjust_difficulty(self.state.current_difficulty, evaluation["score"])
        termination = self.state.should_terminate()
        if termination["terminate"]:
            self.state.status = "terminated"
        if self.state.question_number >= 10 and self.state.status != "terminated":
            self.state.status = "finished"
        return {
            "evaluation": evaluation,
            "explanation": explanation,
            "next_difficulty": self.state.current_difficulty,
            "status": self.state.status,
            "termination_reason": termination["reason"],
        }

    def finish_interview(self) -> Dict[str, any]:
        timeline = [vars(entry) for entry in self.state.question_history]
        self.state.dna_profile = calculate_dna_profile(
            timeline, 
            self.skill_match,
            integrity_score=self.state.integrity_score,
            plagiarism_flags=self.state.plagiarism_flags,
            time_anomaly_flags=self.state.time_anomaly_flags
        )
        return self.state.dna_profile

    def session_summary(self) -> Dict[str, any]:
        return {
            "resume_profile": self.resume_profile,
            "job_profile": self.job_profile,
            "skill_match": self.skill_match,
            "interview_status": self.state.status,
            "questions_answered": len(self.state.question_history),
            "total_score": round(self.state.total_score, 1),
            "timeline": self.state.build_timeline(),
            "dna_profile": self.state.dna_profile,
        }
