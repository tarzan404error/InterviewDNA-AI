import json
import os
from datetime import datetime


def save_json_report(data: dict, candidate_name: str = None, filename: str = None, folder: str = None) -> str:
    """Save interview report to storage folder organized by candidate name."""
    base_folder = folder or os.path.join(os.getcwd(), "storage")
    
    # Create candidate folder if name provided
    if candidate_name:
        # Sanitize candidate name for folder path
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).strip()
        folder = os.path.join(base_folder, safe_name)
    else:
        folder = base_folder
    
    os.makedirs(folder, exist_ok=True)
    filename = filename or f"interview_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    return path


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
