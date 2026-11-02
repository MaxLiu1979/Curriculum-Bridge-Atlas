#!/usr/bin/env python3
"""Check public package integrity, cross-references, exports and exposure boundaries."""
import csv
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "exports/graph.json").read_text(encoding="utf-8"))
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    maps = {}
    for group in ("concepts", "occurrences", "sources", "cards"):
        rows = data[group]
        maps[group] = {r["id"]: r for r in rows}
        check(len(maps[group]) == len(rows), f"Duplicate IDs in {group}")
        check(data["counts"][group] == len(rows), f"Bad count: {group}")
        for row in rows:
            check((ROOT / row["note"]).is_file(), f"Missing note: {row['id']}")
    cm, om, sm = maps["concepts"], maps["occurrences"], maps["sources"]
    for c in cm.values():
        check(all(i in cm for i in c["prerequisite_ids"]), f"Unresolved prerequisite: {c['id']}")
        check(all(i in om for i in c["occurrence_ids"]), f"Unresolved occurrence: {c['id']}")
        for oid in c["occurrence_ids"]:
            if oid in om:
                check(c["id"] in om[oid]["concept_ids"], f"Asymmetric concept link: {c['id']} -> {oid}")
    missing_source = 0
    for o in om.values():
        if o["source_id"]:
            check(o["source_id"] in sm, f"Unresolved source: {o['id']}")
        else:
            missing_source += 1
        check(all(i in cm for i in o["concept_ids"]), f"Unresolved concept: {o['id']}")
        check(o["stage"] in data["stages"], f"Unknown stage: {o['id']}")
        if o.get("week_in_plan"):
            check(bool(o.get("timing_status")), f"Unqualified example week: {o['id']}")
    for r in data["cards"]:
        check(all(i in cm for i in r["concept_ids"]), f"Unresolved resource concept: {r['id']}")
    for s in sm.values():
        check(bool(re.fullmatch(r"[a-f0-9]{64}", s["sha256"])), f"Invalid source hash: {s['id']}")
    nodes = {n["id"]: n for n in graph["nodes"]}
    check(len(nodes) == len(graph["nodes"]), "Duplicate graph node ID")
    check(len({e["id"] for e in graph["edges"]}) == len(graph["edges"]), "Duplicate graph edge ID")
    for n in nodes.values():
        check((ROOT / n["note"]).is_file(), f"Missing graph note: {n['id']}")
    for e in graph["edges"]:
        check(e["source"] in nodes and e["target"] in nodes, f"Dangling edge: {e['id']}")
    for name, rows in (("nodes", graph["nodes"]), ("edges", graph["edges"])):
        with (ROOT / f"exports/{name}.csv").open(encoding="utf-8-sig", newline="") as handle:
            check(len(list(csv.DictReader(handle))) == len(rows), f"CSV count mismatch: {name}")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', html, re.S)
    check(bool(match) and json.loads(match.group(1)) == data, "Viewer does not embed the current public data")
    spec = importlib.util.spec_from_file_location("public_query", ROOT / "scripts/query.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for term in ["光合作用", "photosynthesis", "quadratic equation", "velocity", "buffer", "opportunity cost", "matrix"]:
        check(module.query(data, term)["matched_count"] > 0, f"Search misses documented example: {term}")
    check(module.query(data, "photosynthesis")["results"][0]["concept"]["id"] == module.query(data, "光合作用")["results"][0]["concept"]["id"], "Chinese/English aliases resolve to different concepts")
    check(module.query(data, "xyzzynonexistentconcept12345")["matched_count"] == 0, "Unknown query returns an unrelated concept")

    forbidden_keys = {"original_paths", "attachment", "source_snapshots", "source_evidence_summary", "raw_text", "teaching_records", "actual_taught_on", "reported_by", "class_code", "source_data_file", "resource_paths", "source_path", "path"}

    def visit(value, trail="data"):
        if isinstance(value, dict):
            for k, v in value.items():
                check(k not in forbidden_keys, f"Forbidden public field: {trail}.{k}")
                visit(v, f"{trail}.{k}")
        elif isinstance(value, list):
            for v in value:
                visit(v, trail)
        elif isinstance(value, str):
            check(not re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|\\\\[^\\\s]+\\", value), f"Local path leaked: {trail}")

    visit(data)
    visit(graph, "graph")
    secret_patterns = [r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"sk-proj-[A-Za-z0-9_-]{20,}", r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"]
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(p in {".git", "__pycache__", "node_modules"} for p in relative.parts):
            continue
        check(path.suffix.lower() not in {".pdf", ".docx", ".xlsx", ".zip", ".env"}, f"Unexpected restricted artifact: {relative}")
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for pattern in secret_patterns:
            check(not re.search(pattern, text), f"Possible secret in {relative}")
        check(not re.search(r"[A-Z]:\\(?:Users|0-cc|BaiduSyncdisk)|wxid[_]|W[e]Chat Files", text), f"Private filesystem reference in {relative}")
    result = {"status": "passed" if not errors else "failed", **data["counts"],
              "nodes": len(nodes), "edges": len(graph["edges"]),
              "occurrences_without_source": missing_source, "errors": errors,
              "scope": "Package structure, public field boundaries and documented search examples; not a re-audit of curriculum claims or classroom effectiveness."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
