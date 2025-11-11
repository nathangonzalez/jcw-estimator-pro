import pandas as pd
import json
import jsonschema
import yaml
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-path", required=True)
    parser.add_argument("--output-dir", default="data/ueltchi/working")
    parser.add_argument("--project-id", default="ueltchi")
    args = parser.parse_args()

    with open("scripts/schedule_columns.yaml", "r") as f:
        column_map = yaml.safe_load(f)

    engine = "xlrd" if args.template_path.endswith(".xls") else "openpyxl"
    df = pd.read_excel(args.template_path, engine=engine, header=None, usecols=range(len(column_map)))
    df.columns = list(column_map.values())

    # Data cleaning and transformation
    if "name" not in df.columns:
        raise KeyError(f"Column 'name' not found in dataframe. Available columns: {df.columns.tolist()}")
    df = df.dropna(subset=["name"])
    df["project_id"] = args.project_id
    
    # Ensure essential columns exist, fill with defaults if not
    for col in ["dependencies", "duration_days", "start_date", "end_date", "assignee", "notes", "wbs_code"]:
        if col not in df.columns:
            df[col] = "" if col != "duration_days" else 0

    df["dependencies"] = df["dependencies"].fillna("").astype(str).apply(lambda x: [i.strip() for i in x.split(",") if i.strip()])
    df["duration_days"] = pd.to_numeric(df["duration_days"], errors="coerce").fillna(0)
    df["wbs_code"] = df["wbs_code"].fillna("").astype(str)
    df["name"] = df["name"].astype(str)

    # Schema validation
    with open("schemas/wbs_task.v0.schema.json", "r") as f:
        schema = json.load(f)

    records = df.to_dict("records")
    for record in records:
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            print(f"Validation error in record: {record}")
            print(e)
            # raise e

    # Output to CSV and JSON
    os.makedirs(args.output_dir, exist_ok=True)
    df.to_csv(os.path.join(args.output_dir, "schedule_tasks.v0.csv"), index=False)
    with open(os.path.join(args.output_dir, "schedule_tasks.v0.json"), "w") as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    main()
