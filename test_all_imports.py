"""Test imports"""
try:
    from core.document_validator import validate_is_resume, calculate_resume_accuracy
    from app import show_report, sidebar_controls
    print("ALL_IMPORTS_OK")
except Exception as e:
    print(f"ERROR: {str(e)[:100]}")
