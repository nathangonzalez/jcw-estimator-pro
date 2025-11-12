import json
import jsonschema
import pandas as pd

def test_estimate_lines_schema():
    with open("schemas/estimate_line.v0.schema.json", "r") as f:
        schema = json.load(f)
    
    df = pd.read_csv("data/ueltchi/working/estimate_lines.v0.csv")
    records = df.to_dict("records")
    
    for record in records:
        jsonschema.validate(instance=record, schema=schema)

def test_schedule_tasks_schema():
    with open("schemas/wbs_task.v0.schema.json", "r") as f:
        schema = json.load(f)
        
    df = pd.read_csv("data/ueltchi/working/schedule_tasks.v0.csv")
    records = df.to_dict("records")
    
    for record in records:
        jsonschema.validate(instance=record, schema=schema)
