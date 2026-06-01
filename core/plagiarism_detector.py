import re
from typing import Dict, List


def detect_plagiarism(answer: str, threshold: float = 0.85) -> Dict[str, any]:
    """
    Detect suspicious patterns that indicate copy-paste or plagiarism.
    """
    if not answer.strip():
        return {"is_suspicious": False, "score": 0.0, "reason": ""}

    answer_lower = answer.lower().strip()
    
    # Check for common phrases that indicate copied content
    suspicious_phrases = [
        "according to wikipedia",
        "as per the documentation",
        "copy and paste",
        "ctrl+c",
        "from the internet",
        "google says",
        "stack overflow",
        "i found this",
        "https://",
        "http://",
        "www.",
        "chatgpt",
        "gemini",
        "claude",
    ]
    
    phrase_count = sum(1 for phrase in suspicious_phrases if phrase in answer_lower)
    
    # Check for excessive punctuation or formatting irregularities
    code_block_count = answer.count("```") + answer.count("```")
    
    # Check for unusual patterns
    lines = answer.split("\n")
    
    # Too many empty lines
    empty_lines = sum(1 for line in lines if not line.strip())
    
    # Calculate suspicion score
    suspicion_score = 0.0
    reason_parts = []
    
    if phrase_count > 0:
        suspicion_score += phrase_count * 0.15
        reason_parts.append(f"Contains {phrase_count} suspicious phrase(s)")
    
    if code_block_count > 2:
        suspicion_score += 0.1
        reason_parts.append("Excessive code formatting")
    
    if empty_lines > len(lines) * 0.3:
        suspicion_score += 0.1
        reason_parts.append("Unusual line spacing pattern")
    
    # Check if answer is too polished (exact sentence structures, perfect grammar)
    # This is a simplified heuristic
    if len(answer.split()) > 200 and answer.count(",") > len(answer.split()) * 0.15:
        suspicion_score += 0.05
        reason_parts.append("Suspiciously polished language")
    
    is_suspicious = suspicion_score >= threshold
    
    return {
        "is_suspicious": is_suspicious,
        "score": min(1.0, suspicion_score),
        "reason": " | ".join(reason_parts) if reason_parts else "",
        "confidence": min(1.0, suspicion_score),
    }


def detect_time_anomaly(time_taken: float, question_category: str, average_time: float = 30.0) -> Dict[str, any]:
    """
    Detect suspicious time patterns that indicate cheating or anomalies.
    """
    suspicion_score = 0.0
    reason_parts = []
    
    # Too fast for a complex question (likely pasted)
    if question_category in ["Scenario", "Conceptual", "Hard"] and time_taken < 5.0:
        suspicion_score += 0.2
        reason_parts.append(f"Suspiciously fast for {question_category} question ({time_taken:.1f}s)")
    
    # Way too slow (might indicate research or external help)
    if time_taken > 300:  # 5 minutes
        suspicion_score += 0.15
        reason_parts.append(f"Unusually long response time ({time_taken:.1f}s)")
    
    # Check for Goldilocks problem - all answers in narrow time band (suspicious)
    # This would be checked in the context of interview history
    
    return {
        "is_suspicious": suspicion_score >= 0.2,
        "score": min(1.0, suspicion_score),
        "reason": " | ".join(reason_parts) if reason_parts else "",
        "time_efficiency_adjusted": suspicion_score > 0,
    }


def extract_keywords_from_answer(answer: str) -> List[str]:
    """
    Extract meaningful keywords from an answer for plagiarism and consistency checks.
    """
    # Remove common words
    common = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are", "was", "be", "been", "have", "has", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those"}
    
    # Extract words
    words = re.findall(r"\b[a-z]{4,}\b", answer.lower())
    
    # Filter common words
    keywords = [w for w in words if w not in common]
    
    return list(set(keywords))
