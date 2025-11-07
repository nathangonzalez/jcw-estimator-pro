# Vendor Quotes — LYNN-001

Place raw PDF quotes under `*/raw/`. Use the parser to create JSON under `*/parsed/`, then normalize to CSV under `*/normalized/`. Aggregate all normalized CSVs into `quotes.canonical.csv` with header:

vendor,trade,item,description,unit,qty,unit_cost,line_total,notes
