"""
Document Validator - Detects if uploaded document is a valid resume
and calculates resume accuracy/completeness percentage.
"""
import re
from typing import Dict, List


RESUME_KEYWORDS = {
    "experience": ["experience", "work history", "employment", "job", "position", "worked as", "senior", "junior"],
    "skills": ["skills", "technical skills", "competencies", "expertise", "proficient", "proficiency"],
    "education": ["education", "degree", "university", "college", "school", "graduated", "diploma", "certification"],
    "contact": ["email", "phone", "linkedin", "address", "github", "portfolio", "website"],
    "professional": ["professional", "summary", "objective", "profile", "about", "introduction"],
    "achievement": ["achievement", "accomplishment", "project", "award", "recognition", "responsibility"]
}

EXPECTED_RESUME_SECTIONS = [
    "experience",
    "skills", 
    "education",
    "contact"
]

NON_RESUME_PATTERNS = [
    r"^(Dear|To Whom|Hello Hiring)",  # Letter format
    r"(cover letter|motivation letter)",  # Explicit cover letter
    r"(I am writing to express|I am excited to apply|I am very interested)",  # Cover letter phrases
    r"^(table of contents|table of content)",  # Structural docs
]

# Academic patterns - only flag if multiple are present
ACADEMIC_PATTERNS = [
    r"\b(abstract|abstract:)\b",
    r"\b(methodology|methods)\b",
    r"\b(conclusion|conclusions)\b",
    r"\b(references|bibliography)\b",
]


def validate_is_resume(text: str) -> Dict:
    """
    Validates if uploaded document is actually a resume.
    
    Returns dict with:
    - is_valid: bool (True if likely a resume)
    - confidence: float (0-1, confidence score)
    - reason: str (explanation)
    - document_type: str (detected type: resume, cover_letter, other, etc.)
    """
    if not text or len(text.strip()) < 100:
        return {
            "is_valid": False,
            "confidence": 0.0,
            "reason": "Document too short or empty",
            "document_type": "empty"
        }
    
    text_lower = text.lower()
    
    # Check for definite non-resume patterns (strong indicators)
    for pattern in NON_RESUME_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
            # Only reject if it's clearly a cover letter
            if any(term in text_lower for term in ["dear", "to whom", "hello hiring", "i am writing", "i am excited", "i am very interested"]):
                return {
                    "is_valid": False,
                    "confidence": 0.95,
                    "reason": "Detected as cover letter, not resume",
                    "document_type": "cover_letter"
                }
    
    # Check for academic papers only if MULTIPLE indicators present
    academic_count = 0
    for pattern in ACADEMIC_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            academic_count += 1
    
    # Only flag as academic paper if 3+ academic markers present
    if academic_count >= 3:
        return {
            "is_valid": False,
            "confidence": 0.85,
            "reason": "Detected as academic paper, not resume",
            "document_type": "academic"
        }
    
    # Count resume keywords
    keyword_score = 0.0
    found_sections = []
    
    for section, keywords in RESUME_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + keyword + r'\b', text_lower):
                found_sections.append(section)
                keyword_score += 1
                break
    
    found_sections = list(set(found_sections))
    
    # Check for structured resume elements
    has_dates = len(re.findall(r'\b(20\d{2}|19\d{2})\b', text)) >= 2
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text))
    
    contact_elements = sum([has_email, has_phone])
    
    # Calculate confidence - more lenient now
    section_coverage = len(found_sections) / len(EXPECTED_RESUME_SECTIONS)
    keyword_presence = keyword_score / len(RESUME_KEYWORDS)
    structure_score = (contact_elements / 2.0 + (1.0 if has_dates else 0.0)) / 2.0
    
    confidence = (section_coverage * 0.4) + (keyword_presence * 0.3) + (structure_score * 0.3)
    confidence = min(1.0, max(0.0, confidence))
    
    # Accept resumes with lower confidence threshold (0.3 instead of 0.5)
    is_valid = confidence >= 0.3 or len(found_sections) >= 2
    
    if is_valid:
        reason = f"Resume detected. Found {len(found_sections)}/4 expected sections with {int(confidence*100)}% confidence."
    else:
        reason = f"Document validity: {int(confidence*100)}% (Found {len(found_sections)}/4 sections). Analysis will proceed."
    
    return {
        "is_valid": is_valid,
        "confidence": confidence,
        "reason": reason,
        "document_type": "resume" if is_valid else "unknown"
    }


def calculate_resume_accuracy(text: str) -> Dict:
    """
    Calculates resume completeness and accuracy percentage.
    
    Returns dict with:
    - overall_accuracy: float (0-100, percentage)
    - section_scores: dict (accuracy % for each section)
    - missing_sections: list (sections not found)
    - recommendations: list (suggestions for improvement)
    - quality_level: str (Basic/Good/Excellent)
    """
    text_lower = text.lower()
    text_length = len(text)
    
    section_scores = {}
    max_score = 100
    deductions = 0
    
    # Check each expected section
    for section in EXPECTED_RESUME_SECTIONS:
        keywords = RESUME_KEYWORDS[section]
        found = any(re.search(r'\b' + kw + r'\b', text_lower) for kw in keywords)
        
        if found:
            section_scores[section] = 100
        else:
            section_scores[section] = 0
            deductions += 20
    
    # Bonus sections (not required but increase score)
    bonus_sections = {}
    for section in ["professional", "achievement"]:
        keywords = RESUME_KEYWORDS[section]
        found = any(re.search(r'\b' + kw + r'\b', text_lower) for kw in keywords)
        bonus_sections[section] = found
    
    # Calculate deductions based on document quality
    recommendations = []
    
    # Missing contact info
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text))
    
    if not has_email:
        deductions += 5
        recommendations.append("Add email address")
    if not has_phone:
        deductions += 3
        recommendations.append("Add phone number")
    
    # Check for dates
    dates = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
    if len(dates) < 3:
        deductions += 5
        recommendations.append("Add more dates to work/education timeline")
    
    # Check for sufficient length
    if text_length < 500:
        deductions += 5
        recommendations.append("Expand resume with more details")
    elif text_length > 5000:
        deductions += 3
        recommendations.append("Consider condensing resume length")
    
    # Check for achievements/projects
    if not bonus_sections.get("achievement", False):
        deductions += 5
        recommendations.append("Add achievements or project highlights")
    
    # Check for skills quantification
    skill_mentions = len(re.findall(r'(python|java|c\+\+|javascript|sql|aws|docker|kubernetes|react|angular|node)', text_lower))
    if skill_mentions < 3:
        deductions += 3
        recommendations.append("Mention specific technical skills")
    
    # Check for professional summary
    if not bonus_sections.get("professional", False):
        deductions += 3
        recommendations.append("Add professional summary or objective")
    
    # Calculate final accuracy
    overall_accuracy = max(0, min(100, max_score - deductions))
    
    # Determine quality level
    if overall_accuracy >= 85:
        quality_level = "Excellent 🌟"
    elif overall_accuracy >= 70:
        quality_level = "Good ✅"
    else:
        quality_level = "Basic ⚠️"
    
    missing_sections = [s for s in EXPECTED_RESUME_SECTIONS if section_scores[s] == 0]
    
    return {
        "overall_accuracy": overall_accuracy,
        "section_scores": section_scores,
        "missing_sections": missing_sections,
        "recommendations": recommendations[:5],  # Top 5 recommendations
        "quality_level": quality_level,
        "has_email": has_email,
        "has_phone": has_phone,
        "date_count": len(dates),
        "text_length": text_length
    }


def get_document_type_warning(validation_result: Dict) -> str:
    """Returns HTML warning if document is not a valid resume."""
    if validation_result["is_valid"]:
        return ""
    
    doc_type = validation_result.get("document_type", "unknown")
    reason = validation_result.get("reason", "Invalid document")
    confidence = validation_result.get("confidence", 0)
    
    if doc_type == "cover_letter":
        icon = "📝"
        msg = "Cover Letter Detected - Please upload a resume instead"
    elif doc_type == "legal":
        icon = "⚖️"
        msg = "Legal Document Detected - Please upload a resume"
    elif doc_type == "empty":
        icon = "📭"
        msg = "Document is empty or too short"
    else:
        icon = "❌"
        msg = f"Document validation issue - {reason}"
    
    return f"{icon} {msg}"
