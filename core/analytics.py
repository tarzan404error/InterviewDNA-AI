import statistics
from typing import List, Dict


def calculate_adaptability(history: List[Dict]) -> float:
    if len(history) < 2:
        return 50.0
    recoveries = 0
    opportunities = 0
    for previous, current in zip(history, history[1:]):
        if previous["score"] < 60 and current["score"] >= 75:
            recoveries += 1
        if previous["score"] < 70:
            opportunities += 1
    return min(100.0, (recoveries / max(1, opportunities)) * 100.0 + 30.0)


def calculate_consistency(history: List[Dict]) -> float:
    if len(history) < 2:
        return 50.0
    scores = [entry["score"] for entry in history]
    variance = statistics.pvariance(scores)
    return max(0.0, min(100.0, 100.0 - variance * 10))


def calculate_pressure_handling(history: List[Dict]) -> float:
    pressure_scores = [entry["score"] for entry in history if entry["is_pressure"]]
    if not pressure_scores:
        return 50.0
    return sum(pressure_scores) / len(pressure_scores)


def calculate_dna_profile(history: List[Dict], resume_jd_match: float, integrity_score: float = 100.0, plagiarism_flags: int = 0, time_anomaly_flags: int = 0) -> Dict[str, any]:
    if not history:
        return {
            "knowledge_index": 0.0,
            "communication_index": 0.0,
            "adaptability_index": 0.0,
            "confidence_index": 0.0,
            "consistency_index": 0.0,
            "pressure_handling_index": 0.0,
            "final_readiness": 0.0,
            "integrity_score": 100.0,
            "plagiarism_flags": 0,
            "time_anomaly_flags": 0,
            "recommendation": "Needs Improvement",
        }
    accuracy = [entry["accuracy"] for entry in history]
    depth = [entry["depth"] for entry in history]
    clarity = [entry["clarity"] for entry in history]
    relevance = [entry["relevance"] for entry in history]
    scores = [entry["score"] for entry in history]
    knowledge_index = round((sum(accuracy) + sum(depth)) / (2 * len(history)), 1)
    communication_index = round((sum(clarity) + sum(relevance)) / (2 * len(history)), 1)
    adaptability_index = round(calculate_adaptability(history), 1)
    consistency_index = round(calculate_consistency(history), 1)
    pressure_handling_index = round(calculate_pressure_handling(history), 1)
    confidence_index = round(min(100.0, (sum(scores) / len(scores)) * 0.95 + resume_jd_match * 0.05), 1)
    
    # Apply integrity penalty
    integrity_adjusted_confidence = confidence_index * (integrity_score / 100.0)
    
    readiness = round((knowledge_index * 0.22 + communication_index * 0.2 + adaptability_index * 0.15 + integrity_adjusted_confidence * 0.15 + consistency_index * 0.14 + pressure_handling_index * 0.14), 1)

    if readiness >= 85 and plagiarism_flags == 0 and time_anomaly_flags == 0:
        recommendation = "Strongly Recommended"
    elif readiness >= 70 and plagiarism_flags <= 1:
        recommendation = "Recommended"
    else:
        recommendation = "Needs Improvement"

    # Base heuristic fallback values
    strengths = []
    weaknesses = []
    if knowledge_index >= 80:
        strengths.append("Deep technical knowledge")
    if communication_index >= 80:
        strengths.append("Clear and relevant communication")
    if adaptability_index >= 70:
        strengths.append("Quick recovery after weak answers")
    if consistency_index >= 75:
        strengths.append("Stable performance across questions")
    if pressure_handling_index >= 70:
        strengths.append("Strong pressure resilience")
    if plagiarism_flags == 0 and time_anomaly_flags == 0:
        strengths.append("High interview integrity")
        
    if knowledge_index < 60:
        weaknesses.append("Technical depth needs improvement")
    if communication_index < 60:
        weaknesses.append("Communication could be more concise and structured")
    if adaptability_index < 50:
        weaknesses.append("Adaptability under changing questions is limited")
    if pressure_handling_index < 50:
        weaknesses.append("Pressure handling should be strengthened")
    if plagiarism_flags > 0:
        weaknesses.append(f"Plagiarism risk detected in {plagiarism_flags} answer(s)")
    if time_anomaly_flags > 0:
        weaknesses.append(f"Suspicious time patterns detected in {time_anomaly_flags} answer(s)")

    improvement_areas = [
        "Use more domain-specific terms when answering technical questions.",
        "Focus on structured, complete answers with measurable outcomes.",
        "Practice time-managed responses for tighter delivery.",
    ]

    # Try utilizing Gemini API for hyper-personalized report card insights
    try:
        import json
        from core.gemini_client import GeminiClient
        from core.parser import clean_json_response
        
        client = GeminiClient()
        if client.api_key:
            qa_summary = []
            for entry in history:
                qa_summary.append(
                    f"Question: {entry.get('text', 'N/A')}\n"
                    f"Answer: {entry.get('answer', 'N/A')}\n"
                    f"Score: {entry.get('score', 0)}\n"
                    f"Feedback: {entry.get('explanation', 'N/A')}\n"
                )
            
            prompt = f"""
            You are an expert HR strategist and organizational psychologist. Analyze the candidate's interview transcript and generate deep, personalized performance insights.
            
            Interview Transcript:
            {"---NEXT QUESTION---\n".join(qa_summary)}
            
            Overall Metrics:
            - Knowledge Index: {knowledge_index}
            - Communication Index: {communication_index}
            - Adaptability Index: {adaptability_index}
            - Consistency Index: {consistency_index}
            - Pressure Handling Index: {pressure_handling_index}
            - Final Readiness Score: {readiness}%
            - Plagiarism Flags: {plagiarism_flags}
            - Time Anomaly Flags: {time_anomaly_flags}
            
            Provide:
            1. 3-4 specific technical or behavioral strengths shown by the candidate in their answers.
            2. 2-3 genuine areas of weakness or missing details noticed in their answers.
            3. 3 concrete, personalized action items they should execute to improve their hiring readiness for this target role.
            
            Return your response in clean JSON format. Do not return any extra conversation.
            
            JSON Schema:
            {{
                "strengths": ["Strength 1", "Strength 2", ...],
                "weaknesses": ["Weakness 1", "Weakness 2", ...],
                "improvement_areas": ["Action item 1", "Action item 2", ...]
            }}
            """
            response = client.generate(prompt, temperature=0.3, max_output_tokens=700)
            cleaned = clean_json_response(response)
            data = json.loads(cleaned)
            if all(k in data for k in ["strengths", "weaknesses", "improvement_areas"]):
                strengths = [str(s) for s in data["strengths"]]
                weaknesses = [str(w) for w in data["weaknesses"]]
                improvement_areas = [str(i) for i in data["improvement_areas"]]
    except Exception:
        pass

    return {
        "knowledge_index": knowledge_index,
        "communication_index": communication_index,
        "adaptability_index": adaptability_index,
        "confidence_index": confidence_index,
        "consistency_index": consistency_index,
        "pressure_handling_index": pressure_handling_index,
        "final_readiness": readiness,
        "integrity_score": integrity_score,
        "plagiarism_flags": plagiarism_flags,
        "time_anomaly_flags": time_anomaly_flags,
        "recommendation": recommendation,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_areas": improvement_areas,
    }


def build_timeline(history: List[Dict]) -> Dict[str, List]:
    return {
        "question": [f"Q{entry['question_id']}" for entry in history],
        "difficulty": [entry["difficulty"] for entry in history],
        "score": [entry["score"] for entry in history],
        "time_taken": [entry["time_taken"] for entry in history],
    }
