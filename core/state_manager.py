from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class QuestionHistory:
    question_id: int
    category: str
    difficulty: str
    text: str
    score: float
    accuracy: float
    clarity: float
    depth: float
    relevance: float
    time_taken: float
    is_pressure: bool
    answer: str
    explanation: str
    is_plagiarism_suspicious: bool = False
    is_time_anomaly_suspicious: bool = False
    plagiarism_risk: float = 0.0
    time_anomaly_risk: float = 0.0


@dataclass
class InterviewState:
    status: str = "not_started"
    current_question: Dict = field(default_factory=dict)
    current_difficulty: str = "Easy"
    total_score: float = 0.0
    consecutive_failures: int = 0
    unanswered_count: int = 0
    question_number: int = 0
    pressure_mode: bool = False
    start_time: float = 0.0
    last_question_time: float = 0.0
    question_history: List[QuestionHistory] = field(default_factory=list)
    dna_profile: Dict = field(default_factory=dict)
    resume_jd_match: float = 0.0
    interview_log: List[Dict] = field(default_factory=list)
    plagiarism_flags: int = 0
    time_anomaly_flags: int = 0
    integrity_score: float = 100.0

    def begin(self, initial_difficulty: str, resume_jd_match: float):
        self.status = "running"
        self.current_difficulty = initial_difficulty
        self.total_score = 0.0
        self.consecutive_failures = 0
        self.unanswered_count = 0
        self.question_number = 0
        self.pressure_mode = False
        self.start_time = datetime.utcnow().timestamp()
        self.last_question_time = self.start_time
        self.question_history = []
        self.dna_profile = {}
        self.resume_jd_match = resume_jd_match
        self.interview_log = []

    def record_question(self, question: Dict):
        self.current_question = question
        self.question_number += 1
        self.last_question_time = datetime.utcnow().timestamp()

    def record_answer(self, history: QuestionHistory):
        self.question_history.append(history)
        self.total_score += history.score
        self.last_question_time = datetime.utcnow().timestamp()
        poor_answer = history.score < 60 or history.answer.strip() == ""
        if history.answer.strip() == "":
            self.unanswered_count += 1
        if poor_answer:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        if history.score >= 80 and len(self.question_history) >= 3:
            self.pressure_mode = True
        
        # Track integrity flags (these would be set from evaluator results)
        if hasattr(history, 'is_plagiarism_suspicious') and history.is_plagiarism_suspicious:
            self.plagiarism_flags += 1
            self.integrity_score -= 5
        if hasattr(history, 'is_time_anomaly_suspicious') and history.is_time_anomaly_suspicious:
            self.time_anomaly_flags += 1
            self.integrity_score -= 3

    def current_average(self) -> float:
        if not self.question_history:
            return 0.0
        return self.total_score / len(self.question_history)

    def should_terminate(self) -> Dict[str, any]:
        if self.consecutive_failures >= 3:
            return {"terminate": True, "reason": "Multiple consecutive weak answers"}
        if self.unanswered_count >= 2:
            return {"terminate": True, "reason": "Too many unanswered questions"}
        if len(self.question_history) >= 10:
            return {"terminate": False, "reason": "completed"}
        if self.current_average() < 45 and len(self.question_history) >= 5:
            return {"terminate": True, "reason": "Consistently poor performance"}
        return {"terminate": False, "reason": None}

    def build_timeline(self) -> List[Dict]:
        return [vars(history) for history in self.question_history]
