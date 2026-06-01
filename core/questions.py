from typing import List, Dict
from core.extended_questions import INTERVIEW_QUESTIONS

QUESTION_LIBRARY = INTERVIEW_QUESTIONS

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


def get_questions_by_difficulty(difficulty: str, category: str = None) -> List[Dict]:
    return [q for q in QUESTION_LIBRARY if q["difficulty"] == difficulty and (category is None or q["category"] == category)]


import json
from core.gemini_client import GeminiClient

def select_next_question(
    used_questions: List[int], 
    difficulty: str, 
    pressure_mode: bool = False,
    resume_profile: Dict = None,
    job_profile: Dict = None
) -> Dict:
    pool = [q for q in QUESTION_LIBRARY if q["difficulty"] == difficulty and q["id"] not in used_questions]
    if pressure_mode:
        pool = [q for q in pool if q["category"] == "Scenario"] or pool
    if not pool:
        for level in DIFFICULTY_ORDER:
            pool = [q for q in QUESTION_LIBRARY if q["difficulty"] == level and q["id"] not in used_questions]
            if pool:
                break
    base_q = pool[0] if pool else None
    if not base_q:
        return None
        
    if not resume_profile or not job_profile:
        return base_q
        
    try:
        client = GeminiClient()
        if not client.api_key:
            return base_q
            
        category = base_q["category"]
        resume_skills = ", ".join(resume_profile.get("skills", []))
        resume_projects = "; ".join(resume_profile.get("projects", []))
        jd_skills = ", ".join(job_profile.get("required_skills", []))
        experience_level = job_profile.get("experience_level", "Mid")
        
        prompt = f"""
        You are a highly experienced technical interviewer. Generate a highly tailored interview question for a candidate.
        
        Candidate Resume Details:
        - Professional Title: {resume_profile.get('title', 'Professional')}
        - Skills: {resume_skills}
        - Key Projects / Highlights: {resume_projects}
        
        Target Role Details (Job Description):
        - Required Skills: {jd_skills}
        - Experience Level: {experience_level}
        
        Question Requirements:
        - Category: {category} (Technical, Conceptual, Behavioral, or Scenario)
        - Difficulty: {difficulty}
        
        The question MUST be highly specific to the candidate's technical skills, their project experience, and the job description. Do not ask generic questions. For Technical/Conceptual, focus on deep concepts or practical code scenarios within their stack. For Behavioral/Scenario, connect the situation to their past projects or the target role's expectations.
        
        Return your response in clean JSON format. Do not return any extra conversation.
        
        JSON Schema:
        {{
            "id": {base_q["id"]},
            "text": "Specific, tailored question text here",
            "category": "{category}",
            "difficulty": "{difficulty}",
            "topics": ["keyword1", "keyword2", "keyword3", "concept1", "concept2"]  // 4-8 specific technical keywords or details expected in a correct response, for grading purposes
        }}
        """
        response = client.generate(prompt, temperature=0.3, max_output_tokens=500)
        from core.parser import clean_json_response
        cleaned = clean_json_response(response)
        data = json.loads(cleaned)
        
        if all(k in data for k in ["id", "text", "category", "difficulty", "topics"]):
            return {
                "id": int(data["id"]),
                "text": str(data["text"]),
                "category": str(data["category"]),
                "difficulty": str(data["difficulty"]),
                "topics": [str(t) for t in data["topics"]],
                "skill_level": experience_level
            }
    except Exception:
        pass
        
    return base_q


def adjust_difficulty(current_difficulty: str, last_score: float) -> str:
    index = DIFFICULTY_ORDER.index(current_difficulty)
    if last_score >= 80 and index < len(DIFFICULTY_ORDER) - 1:
        return DIFFICULTY_ORDER[index + 1]
    if last_score < 60 and index > 0:
        return DIFFICULTY_ORDER[index - 1]
    return current_difficulty
