import pandas as pd
import os
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default="data/ueltchi/working/schedule_tasks.v0.csv")
    parser.add_argument("--output-dir", default="output/ueltchi")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    os.makedirs(args.output_dir, exist_ok=True)

    # SCHEDULE_GANTT.xlsx
    df.to_excel(os.path.join(args.output_dir, "SCHEDULE_GANTT.xlsx"), index=False, sheet_name="Schedule")

    # SCHEDULE_SUMMARY.md
    with open(os.path.join(args.output_dir, "SCHEDULE_SUMMARY.md"), "w") as f:
        f.write("# Schedule Summary\n\n")
        f.write(df.to_markdown(index=False))

    # schedule.json
    records = df.to_dict("records")
    with open(os.path.join(args.output_dir, "schedule.json"), "w") as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    main()
