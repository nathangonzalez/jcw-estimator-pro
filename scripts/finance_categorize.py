import argparse
import pandas as pd
import yaml
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rules', required=True)
    parser.add_argument('--inout', required=True)
    args = parser.parse_args()

    with open(args.rules, 'r') as f:
        rules_data = yaml.safe_load(f)

    df = pd.read_csv(args.inout)
    df['category'] = df['category'].astype(str)

    for idx, row in df.iterrows():
        desc = str(row['description']).lower()
        category = rules_data.get('default_category', 'other')
        for rule in rules_data.get('rules', []):
            if re.search(rule['match'], desc, re.IGNORECASE):
                category = rule['category']
                break
        df.at[idx, 'category'] = category

    df.to_csv(args.inout, index=False)

if __name__ == '__main__':
    main()
