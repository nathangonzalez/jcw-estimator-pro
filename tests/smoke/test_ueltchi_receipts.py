import json
import os

def test_receipts_exist():
    assert os.path.exists("output/UELTCHI_MVP_RECEIPT.md")
    assert os.path.exists("output/UELTCHI_STATUS.json")

def test_status_json():
    with open("output/UELTCHI_STATUS.json", "r") as f:
        status = json.load(f)
    
    assert "estimate_lines" in status
    assert "schedule_tasks" in status
    assert "total_estimate" in status
    
    assert isinstance(status["estimate_lines"], int)
    assert isinstance(status["schedule_tasks"], int)
    assert isinstance(status["total_estimate"], (int, float))
