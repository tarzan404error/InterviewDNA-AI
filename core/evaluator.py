import math
import re
from typing import Dict, List
from core.gemini_client import GeminiClient
from core.plagiarism_detector import detect_plagiarism, detect_time_anomaly


def normalize_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 1)))


def score_by_keywords(answer: str, topics: List[str]) -> float:
    answer_lower = answer.lower()
    if not answer_lower.strip():
        return 0.0
    matched = sum(1 for topic in topics if topic.lower() in answer_lower)
    score = matched / max(1, len(topics)) * 100.0
    length_bonus = min(20, len(answer.split()) * 2)
    return normalize_score(score + length_bonus * 0.2)


def calculate_time_efficiency(time_taken: float, asked_time: float = 45.0) -> float:
    if time_taken <= 0:
        return 0.0
    ratio = asked_time / time_taken
    score = min(100.0, ratio * 80 + 20)
    if time_taken > asked_time * 1.5:
        score -= 25
    return normalize_score(score)


import json
from core.gemini_client import GeminiClient
from core.parser import clean_json_response

def evaluate_answer(
    answer: str, 
    topics: List[str], 
    difficulty: str, 
    time_taken: float, 
    is_pressure: bool = False,
    question_text: str = ""
) -> Dict[str, any]:
    answer_text = answer.strip()
    
    # Plagiarism and cheating detection
    plagiarism_check = detect_plagiarism(answer_text, threshold=0.7)
    time_anomaly_check = detect_time_anomaly(time_taken, difficulty)
    
    # Base fallback calculations
    accuracy = score_by_keywords(answer_text, topics)
    relevance = score_by_keywords(answer_text, topics)
    clarity = normalize_score(min(100.0, 40 + len(answer_text.split()) * 1.5)) if answer_text else 0.0
    depth = normalize_score(min(100.0, 30 + len(answer_text.split()) * 1.2 + (10 if difficulty == "Hard" else 0)))
    if len(answer_text.split()) < 6:
        clarity = max(0.0, clarity - 30)
        depth = max(0.0, depth - 30)
    time_score = calculate_time_efficiency(time_taken, asked_time=30.0 if is_pressure else 45.0)
    
    raw_score = (accuracy * 0.3 + clarity * 0.25 + depth * 0.25 + relevance * 0.2) * 0.9 + time_score * 0.1
    explanation = "Accuracy and relevance are weighted strongly, with depth and clarity shaped by answer length and topic coverage."
    
    # Try Gemini evaluation first if answer is provided and key is present
    if answer_text:
        try:
            client = GeminiClient()
            if client.api_key:
                prompt = f"""
                You are an elite technical interviewer. Evaluate the candidate's answer to the following interview question.

                Question: "{question_text}"
                Expected Topics / Keywords: {", ".join(topics)}
                Candidate's Answer: "{answer_text}"
                Difficulty: {difficulty}
                Time Taken by Candidate: {time_taken:.1f} seconds

                Grade the candidate's answer objectively on the following 5 dimensions (from 0 to 100):
                1. Accuracy: Is the response technically correct and precise? (Weight: 30%)
                2. Clarity: Is the explanation concise, well-structured, and easy to understand? (Weight: 25%)
                3. Depth: Does it go beyond surface-level answers and show comprehensive understanding? (Weight: 25%)
                4. Relevance: Does the candidate directly address the specific question asked? (Weight: 20%)
                5. Time Efficiency: Rate their timing (they took {time_taken:.1f}s). An appropriate answer takes 15-45s depending on complexity.

                Calculate a final overall score (0 to 100) based on these weighted criteria. Provide a constructive, professional 1-2 sentence feedback explaining the score.
                If the answer is completely empty, unintelligible, or generic garbage, grade all metrics as 0.

                Return your response in clean JSON format. Do not return any extra conversation.

                JSON Schema:
                {{
                    "accuracy": 85.0,
                    "clarity": 90.0,
                    "depth": 80.0,
                    "relevance": 95.0,
                    "time_efficiency": 85.0,
                    "score": 87.5,
                    "explanation": "Constructive, professional feedback explaining the score and performance."
                }}
                """
                response = client.generate(prompt, temperature=0.2, max_output_tokens=500)
                cleaned = clean_json_response(response)
                data = json.loads(cleaned)
                
                if all(k in data for k in ["accuracy", "clarity", "depth", "relevance", "time_efficiency", "score", "explanation"]):
                    accuracy = float(data["accuracy"])
                    clarity = float(data["clarity"])
                    depth = float(data["depth"])
                    relevance = float(data["relevance"])
                    time_score = float(data["time_efficiency"])
                    raw_score = float(data["score"])
                    explanation = str(data["explanation"])
        except Exception:
            pass

    # Apply plagiarism penalty
    plagiarism_penalty = 0.15 if plagiarism_check["is_suspicious"] else 0.0
    
    # Apply time anomaly penalty
    time_anomaly_penalty = 0.1 if time_anomaly_check["is_suspicious"] else 0.0
    
    # Apply penalties to final score
    final_score = normalize_score((raw_score * (1.0 - plagiarism_penalty - time_anomaly_penalty)))
    
    if not answer_text:
        explanation = "No answer submitted, therefore the evaluation reflects an unanswered question penalty."
    if plagiarism_check["is_suspicious"]:
        explanation += f" ⚠️ Plagiarism risk detected: {plagiarism_check['reason']}"
    if time_anomaly_check["is_suspicious"]:
        explanation += f" ⚠️ Time anomaly: {time_anomaly_check['reason']}"
    
    return {
        "score": final_score,
        "accuracy": accuracy,
        "clarity": clarity,
        "depth": depth,
        "relevance": relevance,
        "time_efficiency": time_score,
        "plagiarism_risk": plagiarism_check["score"],
        "time_anomaly_risk": time_anomaly_check["score"],
        "is_plagiarism_suspicious": plagiarism_check["is_suspicious"],
        "is_time_anomaly_suspicious": time_anomaly_check["is_suspicious"],
        "explanation": explanation,
    }


def explain_score(answer: str, evaluation: Dict[str, any]) -> str:
    return (
        f"Your response scored {evaluation['score']} overall. "
        f"Accuracy: {evaluation['accuracy']}, Clarity: {evaluation['clarity']}, "
        f"Depth: {evaluation['depth']}, Relevance: {evaluation['relevance']}. "
        f"Time efficiency is {evaluation['time_efficiency']}% for the time taken."
    )


def enrich_explanation_with_ai(prompt: str) -> str:
    client = GeminiClient()
    result = client.generate(prompt, temperature=0.2, max_output_tokens=150)
    return result or "The candidate response was analyzed with a deterministic scoring model for transparency."
