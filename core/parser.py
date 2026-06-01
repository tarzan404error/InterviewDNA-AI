import re
from typing import List, Dict

SKILL_KEYWORDS = [
    "python", "java", "javascript", "docker", "kubernetes", "sql", "aws", "gcp",
    "azure", "pandas", "numpy", "react", "node", "machine learning", "data analysis",
    "nlp", "computer vision", "github", "rest api", "microservices", "linux",
    "agile", "scrum", "ci/cd", "tensorflow", "pytorch", "fastapi",
]

LEVEL_KEYWORDS = {
    "Entry": ["junior", "entry", "fresher", "associate", "0-2"],
    "Mid": ["mid", "intermediate", "3-5", "mid-level", "experienced"],
    "Senior": ["senior", "lead", "principal", "5+", "expert"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_lines_by_section(text: str, section_titles: List[str]) -> List[str]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    extracted = []
    for idx, line in enumerate(lines):
        if any(title in line.lower() for title in section_titles):
            for next_line in lines[idx + 1: idx + 15]:
                if any(title in next_line.lower() for title in ["experience", "education", "skill", "project", "summary", "certification"]):
                    break
                extracted.append(next_line)
            break
    return extracted


def extract_skills(text: str) -> List[str]:
    normalized = normalize_text(text)
    skills = set()
    for keyword in SKILL_KEYWORDS:
        if keyword in normalized:
            skills.add(keyword.title())
    skills_pattern = re.compile(r"\b([A-Za-z0-9+\-/\.]{2,30})\b")
    for match in skills_pattern.findall(text):
        token = match.strip()
        if token.lower() in SKILL_KEYWORDS:
            skills.add(token.title())
    return sorted(skills)


def extract_projects(text: str) -> List[str]:
    matches = re.findall(r"(?i)(project[s]?:?)([\s\S]{0,300}?)(?=\n\n|experience|education|certification|skills|$)", text)
    projects = []
    for _, block in matches:
        project_lines = [line.strip() for line in block.split("\n") if line.strip()]
        projects.extend(project_lines[:4])
    return projects[:6]


def extract_education(text: str) -> List[str]:
    educations = []
    for line in text.split("\n"):
        if re.search(r"\b(university|college|b\.sc|m\.sc|bachelor|master|mba|phd|degree|certified)\b", line, re.I):
            educations.append(line.strip())
    return educations[:4]


def extract_experience(text: str) -> List[str]:
    experience = []
    for line in text.split("\n"):
        if re.search(r"\b(years|year|experience|managed|led|developed|designed|built)\b", line, re.I):
            experience.append(line.strip())
    return experience[:6]


def detect_experience_level(text: str) -> str:
    normalized = normalize_text(text)
    for level, tokens in LEVEL_KEYWORDS.items():
        if any(token in normalized for token in tokens):
            return level
    return "Mid"


def extract_keywords(text: str, limit: int = 12) -> List[str]:
    normalized = normalize_text(text)
    tokens = re.findall(r"\b[a-z]{3,15}\b", normalized)
    common = {"and", "the", "for", "with", "from", "that", "this", "using", "based", "role", "job"}
    freq = {}
    for token in tokens:
        if token in common:
            continue
        freq[token] = freq.get(token, 0) + 1
    sorted_tokens = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return [token for token, _ in sorted_tokens[:limit]]


import json
from core.gemini_client import GeminiClient

def clean_json_response(raw_text: str) -> str:
    if not raw_text:
        return ""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return cleaned.strip()

def parse_job_description(text: str) -> Dict[str, any]:
    # Try Gemini parsing first
    try:
        client = GeminiClient()
        prompt = f"""
        You are an expert technical recruiter. Analyze the following Job Description (JD) text and extract the role's requirements in a clean JSON format. Do not return any extra conversation, just the JSON block.

        JSON Schema:
        {{
            "required_skills": ["Skill 1", "Skill 2", ...],
            "responsibilities": ["Responsibility 1", "Responsibility 2", ...],
            "experience_level": "Entry / Mid / Senior",
            "keywords": ["Keyword 1", "Keyword 2", ...]
        }}

        Job Description Text:
        {text}
        """
        response = client.generate(prompt, temperature=0.1, max_output_tokens=600)
        cleaned = clean_json_response(response)
        data = json.loads(cleaned)
        
        # Ensure all expected fields are present
        if all(k in data for k in ["required_skills", "responsibilities", "experience_level", "keywords"]):
            return {
                "raw_text": text,
                "required_skills": [str(s) for s in data["required_skills"]],
                "responsibilities": [str(r) for r in data["responsibilities"]],
                "experience_level": str(data["experience_level"]),
                "keywords": [str(k) for k in data["keywords"]],
            }
    except Exception:
        pass

    # Fallback to deterministic regex-based extraction
    skills = extract_skills(text)
    responsibilities = extract_lines_by_section(text, ["responsibilities", "you will", "job duties", "what you'll do", "expectations"])
    level = detect_experience_level(text)
    keywords = extract_keywords(text)
    return {
        "raw_text": text,
        "required_skills": skills,
        "responsibilities": responsibilities,
        "experience_level": level,
        "keywords": keywords,
    }


def parse_resume_text(text: str) -> Dict[str, any]:
    # Try Gemini parsing first
    try:
        client = GeminiClient()
        prompt = f"""
        You are an expert ATS (Applicant Tracking System) parser. Analyze the following resume text and extract the candidate's professional details in a clean JSON format. Do not return any extra conversation, just the JSON block.

        JSON Schema:
        {{
            "name": "Candidate's full name",
            "title": "Professional title or role (e.g. Senior Software Engineer)",
            "skills": ["Skill 1", "Skill 2", ...],
            "projects": ["Brief summary of Project 1", "Brief summary of Project 2", ...],
            "education": ["Education entry 1", "Education entry 2", ...],
            "experience": ["Work experience entry 1", "Work experience entry 2", ...],
            "summary": ["Professional summary sentence 1", "Professional summary sentence 2", ...]
        }}

        Resume Text:
        {text}
        """
        response = client.generate(prompt, temperature=0.1, max_output_tokens=800)
        cleaned = clean_json_response(response)
        data = json.loads(cleaned)
        
        if all(k in data for k in ["name", "title", "skills", "projects", "education", "experience", "summary"]):
            return {
                "name": str(data["name"]),
                "title": str(data["title"]),
                "skills": [str(s) for s in data["skills"]],
                "projects": [str(p) for p in data["projects"]],
                "education": [str(e) for e in data["education"]],
                "experience": [str(exp) for exp in data["experience"]],
                "summary": [str(s) for s in data["summary"]] if isinstance(data["summary"], list) else [str(data["summary"])],
            }
    except Exception:
        pass

    # Fallback to deterministic regex-based extraction
    skills = extract_skills(text)
    projects = extract_projects(text)
    education = extract_education(text)
    experience = extract_experience(text)
    summary = extract_lines_by_section(text, ["summary", "profile", "about me", "professional summary"])
    name = text.strip().split("\n")[0] if text.strip() else "Candidate"
    title_candidates = [line for line in text.split("\n") if re.search(r"\b(engineer|developer|analyst|scientist|manager|consultant|architect)\b", line, re.I)]
    title = title_candidates[0].strip() if title_candidates else "Professional"
    return {
        "name": name,
        "title": title,
        "skills": skills,
        "projects": projects,
        "education": education,
        "experience": experience,
        "summary": summary,
    }
