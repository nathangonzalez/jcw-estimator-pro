import pandas as pd
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default="data/ueltchi/working/estimate_lines.v0.csv")
    parser.add_argument("--output-dir", default="output/ueltchi")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    os.makedirs(args.output_dir, exist_ok=True)

    # ESTIMATE_SUMMARY.md
    summary = df.groupby("trade")["line_total"].sum().sort_values(ascending=False)
    top_20 = df.sort_values("line_total", ascending=False).head(20)

    with open(os.path.join(args.output_dir, "ESTIMATE_SUMMARY.md"), "w") as f:
        f.write("# Estimate Summary\n\n")
        f.write("## Totals by Trade\n\n")
        f.write(summary.to_markdown())
        f.write("\n\n## Top 20 Line Items\n\n")
        f.write(top_20.to_markdown(index=False))

    # estimate_lines.xlsx
    df.to_excel(os.path.join(args.output_dir, "estimate_lines.xlsx"), index=False, sheet_name="Estimate Lines")

    # proposal.xlsx
    proposal_df = pd.DataFrame({
        "Description": ["Total Project Cost", "Allowances"],
        "Amount": [df["line_total"].sum(), 0] # Placeholder for allowances
    })
    proposal_df.to_excel(os.path.join(args.output_dir, "proposal.xlsx"), index=False, sheet_name="Proposal")

if __name__ == "__main__":
    main()
