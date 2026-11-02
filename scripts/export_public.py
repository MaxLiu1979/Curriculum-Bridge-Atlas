#!/usr/bin/env python3
"""Export an explicitly selected, private atlas to the public schema. Stdlib only.

The source is never copied wholesale. Only reviewed fields below can be exported.
Usage: python scripts/export_public.py --source /path/to/private-vault
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
CONCEPT_FIELDS = "id subject subjects title_zh title_en aliases definition definition_status prerequisite_ids occurrence_ids canonical_status relation_warning first_appearance_rule origin".split()
OCC_FIELDS = "id stage course code title position_label component source_id pdf_pages relation depth_summary expected_outputs gap evidence_status working_code concept_ids first_seen_eligible sequence_rank teaching_position_status depth_band version_note grade term book_position grade_term_status semester_in_plan week_in_plan timing_status timing_precision search_terms".split()
CARD_FIELDS = "concept_id subject title target_course target_course_status target_topics teaching_focus prerequisites diagnostic_task diagnostic_solution common_misconception teaching_activity practice_task practice_solution exit_evidence as_a2_extension board_bridges transfer_rules entry_nodes node_rule data_notice ncuk_bridge scope_limits module_name scope_notes board_bridge_status ncuk_links linked_foundation_modules task_provenance delivery_boundary teaching_boundary".split()
PRIVATE_KEY = re.compile(r"(?:path|attachment|original_paths|source_data_file|source_provenance|source_snapshots|reported_by|class_code|taught_on|actual_taught_on|teaching_records|source_evidence_summary|raw_text|excerpt|quote)", re.I)
LOCAL_PATH = re.compile(r"(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|\\\\[^\\\s]+\\)")
DOMAINS = ("cambridgeinternational.org", "qualifications.pearson.com", "aqa.org.uk", "aqa.org", "oxfordaqa.com", "oxfordaqaexams.org.uk", "ncuk.ac.uk", "pep.com.cn", "smartedu.cn")
OFFICIAL = {
    "Cambridge": "https://www.cambridgeinternational.org/programmes-and-qualifications/",
    "NCUK": "https://www.ncuk.ac.uk/ncuk-programmes/international-foundation-year/",
    "Edexcel": "https://qualifications.pearson.com/",
    "AQA/OxfordAQA": "https://www.aqa.org.uk/",
    "国内教材": "https://basic.smartedu.cn/tchMaterial",
}


def public_url(value):
    parts = urlsplit(value or "")
    host = (parts.hostname or "").lower()
    if parts.scheme == "https" and any(host == d or host.endswith("." + d) for d in DOMAINS):
        return urlunsplit(("https", parts.netloc, parts.path, "", ""))
    return ""


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if not PRIVATE_KEY.search(k)}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        if LOCAL_PATH.search(value):
            return "本机材料路径未公开；请按来源编号与页码自行核对。"
        if value.startswith(("http://", "https://")):
            return public_url(value)
    return value


def select(row, keys):
    return clean({key: row[key] for key in keys if key in row})


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads((args.source / "05_结构化数据/atlas.json").read_text(encoding="utf-8-sig"))
    concepts = [select(c, CONCEPT_FIELDS) for c in source["concepts"]]
    occurrences = [select(o, OCC_FIELDS) for o in source["occurrences"]]
    for c in concepts:
        c["note"] = f"vault/concepts/{c['id']}.md"
    for o in occurrences:
        o["note"] = f"vault/occurrences/{o['id']}.md"
    sources = []
    for s in source["sources"]:
        item = select(s, "id title kind sha256 version_note".split())
        item["url"] = public_url(s.get("url"))
        item["official_entry"] = OFFICIAL[s["kind"]]
        item["access_note"] = "仅公开书目、哈希与定位；原件未随库分发。官方入口不是此哈希原件的下载地址；须核对版本。"
        if s["kind"] == "国内教材":
            item["access_note"] += "部分原件来自第三方托管，原出版与印次信息仍以版本注记为准。"
        if s["kind"] == "NCUK":
            item["access_note"] += "模块材料请向有权提供的课程中心获取。示例周次不是实际授课记录。"
        item["note"] = f"vault/sources/{s['id']}.md"
        sources.append(item)
    cards = []
    for card in source["cards"]:
        item = select(card, "id card_id subject title concept_ids".split())
        item["data"] = select(card["data"], CARD_FIELDS)
        item["note"] = f"vault/resources/{card['card_id']}.md"
        cards.append(item)
    rules = select(source["evidence_rules"], "course_position first_seen time depth teaching_proposal".split())
    rules["public_access"] = "公开版提供独立编写的释义、衔接摘要和练习及原件定位，不附第三方教材、大纲或内部模块原件。"
    rules["validation"] = "结构验证与界面测试不能证明课程等价、学生掌握或课堂效果。证据状态沿用2026-10-25资料快照，本次发布没有重核全部原件。"
    data = {
        "schema_version": "1.0-public", "created": source["created"],
        "published": "2026-11-02", "title": "Curriculum Bridge Atlas", "release": "v1.0.1",
        "subjects": source["subjects"], "stages": source["stages"],
        "concepts": concepts, "occurrences": occurrences, "sources": sources, "cards": cards,
        "evidence_rules": rules,
        "counts": {"concepts": len(concepts), "occurrences": len(occurrences), "sources": len(sources), "cards": len(cards)},
    }
    dump(ROOT / "data/atlas.json", data)
    # Preserve IDs, direction and relation labels, while replacing every note path.
    original_graph = json.loads((args.source / "08_通用导出/graph.json").read_text(encoding="utf-8-sig"))
    note_by_id = {row["id"]: row["note"] for rows in (concepts, occurrences, sources, cards) for row in rows}
    nodes = []
    for n in original_graph["nodes"]:
        item = select(n, "id type label subject subjects aliases stage position depth evidence_status sha256".split())
        item["note"] = note_by_id.get(n["id"], f"vault/subjects/{n['label']}.md")
        nodes.append(item)
    graph = {"schema_version": "1.0-public", "directed": True, "nodes": nodes,
             "edges": [select(e, "id source target relation status evidence_status pdf_pages".split()) for e in original_graph["edges"]],
             "relation_definitions": clean(original_graph["relation_definitions"]),
             "source": "data/atlas.json; 2026-10-25 snapshot, public edition 2026-11-02"}
    dump(ROOT / "exports/graph.json", graph)
    print(json.dumps({**data["counts"], "nodes": len(nodes), "edges": len(graph["edges"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
