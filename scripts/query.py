#!/usr/bin/env python3
"""Search the public atlas locally, with no dependency or network request."""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fold(value):
    return "".join(c for c in unicodedata.normalize("NFKC", str(value)).casefold() if c.isalnum())


def query(data, term, subject=None, limit=12):
    needle = fold(term)
    om = {o["id"]: o for o in data["occurrences"]}
    sm = {s["id"]: s for s in data["sources"]}
    matches = []
    for c in data["concepts"]:
        if subject and subject not in c.get("subjects", [c["subject"]]):
            continue
        terms = [fold(x) for x in [c["id"], c["title_zh"], c["title_en"], *c["aliases"]]]
        score = 100 if needle in terms else 70 if any(needle in t for t in terms) else 0
        if score:
            matches.append((score, c))
    matches.sort(key=lambda x: (-x[0], x[1]["id"]))
    results = []
    for _, c in matches[:limit]:
        rows = [om[i] for i in c["occurrence_ids"]]
        results.append({"concept": c, "occurrences": rows,
                        "sources": [sm[i] for i in sorted({o['source_id'] for o in rows if o['source_id'] in sm})]})
    return {"query": term, "matched_count": len(matches), "results": results,
            "evidence_rules": data["evidence_rules"]}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("term", nargs="+")
    parser.add_argument("--subject")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    data = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    result = query(data, " ".join(args.term), args.subject, args.limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"匹配 {result['matched_count']} 个概念 / 主题组；资料快照 {data['created']}")
        for hit in result["results"]:
            c = hit["concept"]
            print(f"\n{c['id']} · {c['title_zh']} / {c['title_en']}\n{c['definition']}")
            for stage in data["stages"]:
                rows = [o for o in hit["occurrences"] if o["stage"] == stage]
                if rows:
                    print(f"\n[{stage}]")
                    for o in rows:
                        print(f"- {o['position_label']}\n  {o['depth_summary']}\n  {o['relation']}；{o['evidence_status']}\n  来源 {o['source_id']} · PDF页 {o['pdf_pages']}")
        print("\n课程位置与示例周次不能用作实际授课或学生掌握结论。原件未随库分发。")
    return 0 if result["matched_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
