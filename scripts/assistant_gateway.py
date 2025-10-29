#!/usr/bin/env python3
"""
File-driven assistant gateway (stub).
- Reads a list of JSON request files from argv[1] (a text file of paths).
- For each request, writes Markdown + JSON replies into output/assistant/.
- No external API calls.
"""
import json, sys, pathlib, datetime

def load_lines(list_path: str):
    p = pathlib.Path(list_path)
    if not p.exists():
        print(f"[gateway] List file not found: {list_path}")
        return []
    return [line.strip() for line in p.read_text().splitlines() if line.strip()]

def now_utc_stamp():
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def main():
    if len(sys.argv) < 2:
        print("[gateway] usage: assistant_gateway.py ask_files.txt")
        sys.exit(1)

    ask_list_file = sys.argv[1]
    ask_files = load_lines(ask_list_file)
    outdir = pathlib.Path("output/assistant")
    outdir.mkdir(parents=True, exist_ok=True)

    for ask in ask_files:
        try:
            data = json.loads(pathlib.Path(ask).read_text(encoding="utf-8"))
        except Exception as e:
            ts = now_utc_stamp()
            (outdir / f"RESPONSE_{ts}_ERROR.md").write_text(
                f"# Assistant Reply ({ts})\n\n**Error loading request:** `{ask}`\n\n```\n{e}\n```\n",
                encoding="utf-8"
            )
            continue

        ts = now_utc_stamp()
        # Extract fields with safe defaults
        source  = data.get("source", "unknown")
        intent  = data.get("intent", "unspecified")
        context = data.get("context", {})
        prompt  = data.get("prompt", "").strip()
        artifacts = data.get("artifacts", [])

        # Stub response (echo + simple analysis)
        analysis = [
            "Stub gateway processed the request.",
            "No external API calls were made.",
            "Round-trip verified via GitHub Action."
        ]
        decision = "ACK" if prompt else "NO_PROMPT"

        # Write JSON artifact
        json_out = {
            "ts": ts,
            "source": source,
            "intent": intent,
            "context": context,
            "prompt": prompt,
            "decision": decision,
            "analysis": analysis,
            "artifacts": artifacts
        }
        (outdir / f"RESPONSE_{ts}.json").write_text(json.dumps(json_out, indent=2), encoding="utf-8")

        # Write Markdown artifact
        md = []
        md.append(f"# Assistant Reply ({ts})")
        md.append("")
        md.append(f"**Source:** `{source}`  |  **Intent:** `{intent}`  |  **Decision:** `{decision}`")
        md.append("")
        if context:
            md.append("**Context:**")
            md.append("```json")
            md.append(json.dumps(context, indent=2))
            md.append("```")
        if prompt:
            md.append("**Prompt:**")
            md.append("```")
            md.append(prompt)
            md.append("```")
        if artifacts:
            md.append("**Requested Artifacts:**")
            for a in artifacts:
                md.append(f"- `{a}`")
        md.append("")
        md.append("**Notes:**")
        for a in analysis:
            md.append(f"- {a}")
        md.append("")
        (outdir / f"RESPONSE_{ts}.md").write_text("\n".join(md), encoding="utf-8")

        print(f"[gateway] Processed: {ask} -> RESPONSE_{ts}")

if __name__ == "__main__":
    main()
