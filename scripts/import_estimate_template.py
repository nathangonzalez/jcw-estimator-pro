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

    with open("scripts/columns.yaml", "r") as f:
        column_map = yaml.safe_load(f)

    engine = "xlrd" if args.template_path.endswith(".xls") else "openpyxl"
    df = pd.read_excel(args.template_path, engine=engine, header=None)
    df.columns = list(column_map.values())[:len(df.columns)]

    # Data cleaning and transformation
    if "item" not in df.columns:
        raise KeyError(f"Column 'item' not found in dataframe. Available columns: {df.columns.tolist()}")
    df = df.dropna(subset=["item"])
    df["project_id"] = args.project_id
    df["source"] = "template"
    
    # Ensure essential columns exist, fill with defaults if not
    for col in ["qty", "unit_cost", "line_total", "wbs_code", "trade", "unit", "scope_notes", "tags"]:
        if col not in df.columns:
            if col == "tags":
                df[col] = [[] for _ in range(len(df))]
            else:
                df[col] = 0 if col in ["qty", "unit_cost", "line_total"] else ""

    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0)
    df["line_total"] = pd.to_numeric(df["line_total"], errors="coerce").fillna(0)

    df["line_total"] = df.apply(
        lambda row: row["qty"] * row["unit_cost"] if row["line_total"] == 0 else row["line_total"],
        axis=1
    )

    # Schema validation
    with open("schemas/estimate_line.v0.schema.json", "r") as f:
        schema = json.load(f)

    records = df.to_dict("records")
    for record in records:
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            print(f"Validation error in record: {record}")
            print(e)
            # Decide if you want to stop or continue
            # raise e 

    # Output to CSV and JSON
    os.makedirs(args.output_dir, exist_ok=True)
    df.to_csv(os.path.join(args.output_dir, "estimate_lines.v0.csv"), index=False)
    with open(os.path.join(args.output_dir, "estimate_lines.v0.json"), "w") as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    main()
