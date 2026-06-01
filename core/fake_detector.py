import re
from typing import Dict, List


def detect_fake_resume(text: str) -> Dict[str, any]:
    """
    Detect potentially fake or AI-generated resume content.
    """
    if not text.strip():
        return {"is_suspicious": False, "score": 0.0, "reasons": []}
    
    text_lower = text.lower()
    suspicion_score = 0.0
    reasons = []
    
    # Check for generic phrases that are often in fake resumes
    generic_phrases = [
        "responsible for",
        "helped team",
        "worked with",
        "experienced in",
        "proficient in",
        "familiar with",
        "able to",
        "collaborated on",
        "utilized",
        "implemented solution",
        "designed and developed",
    ]
    
    phrase_count = sum(1 for phrase in generic_phrases if phrase in text_lower)
    
    if phrase_count > len(generic_phrases) * 0.6:
        suspicion_score += 0.25
        reasons.append(f"High frequency of generic phrases ({phrase_count})")
    
    # Check for unrealistic skills clustering
    skill_keywords = [
        "python", "java", "javascript", "c++", "go", "rust", "machine learning",
        "data science", "deep learning", "nlp", "cloud", "aws", "gcp", "azure",
        "kubernetes", "docker", "react", "angular", "vue", "sql", "nosql"
    ]
    
    skill_count = sum(1 for skill in skill_keywords if skill in text_lower)
    
    # More than 20 skills in one resume is suspicious
    if skill_count > 20:
        suspicion_score += 0.2
        reasons.append(f"Unrealistic skill count ({skill_count} technologies)")
    
    # Check for date inconsistencies
    year_pattern = r"\b(19|20)\d{2}\b"
    years = [int(y) for y in re.findall(year_pattern, text)]
    
    if years:
        min_year = min(years)
        max_year = max(years)
        
        # Experience claims more than 40 years
        if max_year - min_year > 40:
            suspicion_score += 0.15
            reasons.append(f"Unrealistic experience span ({max_year - min_year} years)")
        
        # Education dates before birth (unlikely)
        if min_year < 1960:
            suspicion_score += 0.1
            reasons.append("Suspiciously old education dates")
    
    # Check for too-perfect formatting
    lines = text.split("\n")
    formatted_lines = sum(1 for line in lines if line and line[0].isupper() and line.count(" ") > 3)
    
    if len(lines) > 0 and formatted_lines / len(lines) > 0.9:
        suspicion_score += 0.1
        reasons.append("Unusually perfect formatting pattern")
    
    # Check for AI writing patterns
    ai_indicators = [
        "seamlessly",
        "orchestrated",
        "leveraged",
        "synergy",
        "paradigm",
        "holistic",
        "innovative",
        "cutting-edge",
        "transformative",
    ]
    
    ai_count = sum(1 for indicator in ai_indicators if indicator in text_lower)
    
    if ai_count >= 5:
        suspicion_score += 0.15
        reasons.append(f"Presence of {ai_count} corporate buzzwords (AI-style language)")
    
    # Check for grammar and spelling
    # Simple heuristic: check for unusual character patterns
    unusual_chars = text.count("@@") + text.count("##") + text.count("$$")
    
    if unusual_chars > 0:
        suspicion_score += 0.1
        reasons.append("Unusual character sequences detected")
    
    return {
        "is_suspicious": suspicion_score >= 0.3,
        "score": min(1.0, suspicion_score),
        "reasons": reasons,
        "confidence": min(1.0, suspicion_score),
    }


def detect_fake_job_description(text: str) -> Dict[str, any]:
    """
    Detect potentially fake or AI-generated job description.
    """
    if not text.strip():
        return {"is_suspicious": False, "score": 0.0, "reasons": []}
    
    text_lower = text.lower()
    suspicion_score = 0.0
    reasons = []
    
    # Check for generic JD patterns
    generic_jd_phrases = [
        "join our team",
        "we are looking for",
        "world-class",
        "passionate about",
        "fast-paced environment",
        "dynamic team",
        "cutting-edge technology",
        "innovative solutions",
        "make an impact",
        "change the world",
    ]
    
    phrase_count = sum(1 for phrase in generic_jd_phrases if phrase in text_lower)
    
    if phrase_count > len(generic_jd_phrases) * 0.5:
        suspicion_score += 0.2
        reasons.append(f"High frequency of generic JD phrases ({phrase_count})")
    
    # Check for missing specifics
    specific_keywords = ["salary", "location", "team size", "reporting to", "contract", "benefits"]
    
    specific_count = sum(1 for keyword in specific_keywords if keyword in text_lower)
    
    if specific_count < 2:
        suspicion_score += 0.15
        reasons.append("Missing key job details (salary, location, etc.)")
    
    # Check for unrealistic requirements
    if "10+ years" in text and "senior" not in text_lower and "lead" not in text_lower:
        suspicion_score += 0.1
        reasons.append("Unrealistic experience requirement for non-senior role")
    
    # Check for too many required skills
    skill_keywords = ["python", "java", "javascript", "sql", "aws", "kubernetes", "react"]
    required_skills = sum(1 for skill in skill_keywords if skill in text_lower)
    
    if required_skills > 10:
        suspicion_score += 0.2
        reasons.append(f"Unrealistic skill requirements ({required_skills} technologies)")
    
    # Check for company name consistency
    company_mentions = text.lower().count("company")
    
    if company_mentions > 5:
        suspicion_score += 0.1
        reasons.append("Generic 'company' references instead of specific name")
    
    return {
        "is_suspicious": suspicion_score >= 0.3,
        "score": min(1.0, suspicion_score),
        "reasons": reasons,
        "confidence": min(1.0, suspicion_score),
    }
