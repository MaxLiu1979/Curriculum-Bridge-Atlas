#!/usr/bin/env python3
"""Check the CIE website data, references, contact profile and preview boundaries."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    author = json.loads((ROOT / "web/author.json").read_text(encoding="utf-8"))
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    maps = {}
    for group in ("concepts", "occurrences", "sources", "cards"):
        rows = data[group]
        maps[group] = {r["id"]: r for r in rows}
        check(len(maps[group]) == len(rows), "Duplicate IDs in " + group)
        check(data["counts"][group] == len(rows), "Bad count: " + group)
    cm, om, sm = maps["concepts"], maps["occurrences"], maps["sources"]
    allowed_stages = {"国内初中", "国内高中", "CIE IGCSE", "CIE AS/A-Level", "CIE Further"}
    check(set(data["stages"]) == allowed_stages, "Website stage scope changed")
    for c in cm.values():
        check(all(i in cm for i in c["prerequisite_ids"]), "Unresolved prerequisite: " + c["id"])
        check(all(i in om for i in c["occurrence_ids"]), "Unresolved location: " + c["id"])
        check(any(om[i]["stage"].startswith("CIE") for i in c["occurrence_ids"] if i in om), "Concept has no direct CIE location: " + c["id"])
        for oid in c["occurrence_ids"]:
            if oid in om:
                check(c["id"] in om[oid]["concept_ids"], "Asymmetric concept link: " + c["id"])
    for o in om.values():
        check(o["source_id"] in sm, "Unresolved source: " + o["id"])
        check(all(i in cm for i in o["concept_ids"]), "Unresolved concept: " + o["id"])
        check(o["stage"] in allowed_stages, "Unknown stage: " + o["id"])
    for s in sm.values():
        check(s["kind"] in {"Cambridge", "国内教材"}, "Unexpected source scope: " + s["id"])
        check(bool(re.fullmatch(r"[a-f0-9]{64}", s["sha256"])), "Invalid source hash: " + s["id"])
    for r in data["cards"]:
        check(all(i in cm for i in r["concept_ids"]), "Unresolved teaching-card concept: " + r["id"])
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', html, re.S)
    check(bool(match) and json.loads(match.group(1)) == data, "Viewer does not embed current website data")
    check(author["name"] == "Max Liu", "Unexpected author name")
    check(author["email"] == "max_liu1979@outlook.com", "Public contact differs from the approved address")
    check(html.count('mailto:' + author["email"]) >= 2, "Contact links missing from the author panels")
    check(author["discussions_url"] in html, "Community link missing")
    check(not re.search(r"__(?:AUTHOR|COUNT|ATLAS)_[A-Z_]+__", html), "Unresolved template placeholder")
    scope_pattern = r"NCUK|Edexcel|OxfordAQA|\bAQA\b|NCX-|ncuk_"
    check(not re.search(scope_pattern, json.dumps(data, ensure_ascii=False), re.I), "Out-of-scope curriculum remains in page data")
    check(not re.search(scope_pattern, re.sub(r'<script.*?</script>', '', html, flags=re.S), re.I), "Out-of-scope curriculum remains in the visible page")
    check(not re.search(r'<a[^>]+(?:download|href=[\"\'][^\"\']*\.(?:zip|pdf|csv|json|canvas)(?:[\"\'?#]))', html, re.I), "File delivery link in website HTML")
    js = (ROOT / "web/viewer.js").read_text(encoding="utf-8")
    check(not any(t in js for t in ['createObjectURL', 'new Blob', '.download=', 'exportConcept', '尚未核到可确定的早期正文', '尚未核到系统讲解的窄主题证据']), "Export control or empty-summary placeholder remains")
    forbidden = {"original_paths", "attachment", "source_snapshots", "source_evidence_summary", "raw_text", "teaching_records", "actual_taught_on", "reported_by", "class_code", "source_data_file", "resource_paths", "source_path", "path", "note"}

    def visit(value):
        if isinstance(value, dict):
            for k, v in value.items():
                check(k not in forbidden, "Forbidden page field: " + k)
                visit(v)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            check(not re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|\\\\[^\\\s]+\\", value), "Local path in page data")
    visit(data)
    for name in ["vault", "exports"]:
        check(not (ROOT / name).exists(), "Legacy file-delivery folder remains: " + name)
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "__pycache__", "node_modules"} for part in path.relative_to(ROOT).parts):
            continue
        check(path.suffix.lower() not in {".pdf", ".docx", ".xlsx", ".zip", ".csv", ".canvas", ".env"}, "Unexpected file-delivery artifact: " + str(path.relative_to(ROOT)))
    print(json.dumps({"status": "passed" if not errors else "failed", **data["counts"], "author": author["name"], "errors": errors, "scope": "CIE website integrity and public fields; not a curriculum re-audit or classroom-effectiveness claim."}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
