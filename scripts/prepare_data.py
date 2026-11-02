#!/usr/bin/env python3
"""Prepare CIE website data from an explicitly selected local curriculum vault."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONCEPT_FIELDS = "id subject subjects title_zh title_en aliases definition definition_status prerequisite_ids occurrence_ids canonical_status relation_warning first_appearance_rule".split()
OCC_FIELDS = "id stage course code title position_label component source_id pdf_pages relation depth_summary expected_outputs gap evidence_status working_code concept_ids first_seen_eligible sequence_rank teaching_position_status depth_band version_note grade term book_position grade_term_status search_terms".split()
CARD_FIELDS = "concept_id subject title target_course target_course_status target_topics teaching_focus prerequisites diagnostic_task diagnostic_solution common_misconception teaching_activity practice_task practice_solution exit_evidence as_a2_extension transfer_rules entry_nodes node_rule data_notice scope_limits module_name scope_notes teaching_boundary".split()
STAGES = ["国内初中", "国内高中", "CIE IGCSE", "CIE AS/A-Level", "CIE Further"]
OUT_OF_SCOPE = re.compile(r"NCUK|Edexcel|OxfordAQA|\bAQA\b|NCX-|ncuk_", re.I)
PRIVATE_KEY = re.compile(r"path|attachment|source_data_file|source_provenance|source_snapshots|reported_by|class_code|taught_on|teaching_records|source_evidence_summary|raw_text|excerpt|quote|url", re.I)
LOCAL_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|\\\\[^\\\s]+\\")


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if not PRIVATE_KEY.search(k)}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        if LOCAL_PATH.search(value):
            return "请按来源编号、页码与版本说明核对原件。"
        value = value.replace("CIE/NCUK", "CIE").replace("AS/A2或NCUK", "AS/A-Level")
        value = value.replace("按as_a2_extension或ncuk_bridge进入升级内容", "按对应 CIE 阶段的升级建议进入后续内容")
        value = value.replace("CIE 0510 / 0500 / 9093按课程分支，NCUK EAP独立路径", "CIE 0510 / 0500 / 9093，按具体课程分支")
        if value.startswith("0510侧重第二语言技能，0500侧重第一语言读写，9093含语言分析与语言学；"):
            value = "CIE 0510 侧重第二语言技能，0500 侧重第一语言读写，9093 含语言分析与语言学。三条课程分别诊断，不能依年级或英语书已学完互认。"
        value = value.replace("本模块prerequisites", "本卡先修要求").replace("practice_task", "迁移练习")
        value = value.split("；NCUK")[0]
    return value


def select(row, keys):
    return clean({k: row[k] for k in keys if k in row})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads((args.source / "05_结构化数据/atlas.json").read_text(encoding="utf-8-sig"))
    eligible = [o for o in source["occurrences"] if o["stage"] in STAGES]
    cie_concepts = {cid for o in eligible if o["stage"].startswith("CIE") for cid in o["concept_ids"]}
    concepts = [select(c, CONCEPT_FIELDS) for c in source["concepts"] if c["id"] in cie_concepts]
    occurrences = [select(o, OCC_FIELDS) for o in eligible if set(o["concept_ids"]) & cie_concepts]
    for o in occurrences:
        o["concept_ids"] = [cid for cid in o["concept_ids"] if cid in cie_concepts]
    occurrence_ids = {o["id"] for o in occurrences}
    for c in concepts:
        c["occurrence_ids"] = [oid for oid in c["occurrence_ids"] if oid in occurrence_ids]
        c["prerequisite_ids"] = [cid for cid in c["prerequisite_ids"] if cid in cie_concepts]
    source_ids = {o["source_id"] for o in occurrences}
    sources = []
    for s in source["sources"]:
        if s["id"] not in source_ids:
            continue
        if s["kind"] not in ("Cambridge", "国内教材"):
            raise ValueError("Unexpected source for the selected CIE scope: " + s["id"])
        item = select(s, "id title kind sha256 version_note".split())
        item["access_note"] = "页面提供书目、页码与版本定位；原件未在此网页提供。所查版本不自动代表现行版或学校采用版。"
        if s["kind"] == "国内教材":
            item["access_note"] += "部分原资料来自第三方托管；出版社、印次和可靠性边界以版本说明为准。"
        sources.append(item)
    cards = []
    for card in source["cards"]:
        if card["card_id"].startswith("NCX-") or not set(card["concept_ids"]) & cie_concepts:
            continue
        item = select(card, "id card_id subject title concept_ids".split())
        item["concept_ids"] = [cid for cid in item["concept_ids"] if cid in cie_concepts]
        item["data"] = select(card["data"], CARD_FIELDS)
        cards.append(item)
    rules = select(source["evidence_rules"], "course_position first_seen time depth teaching_proposal".split())
    rules["course_position"] = "国内教材册次、章节与 CIE 大纲小节属于课程证据，不等于实际授课完成。"
    rules["public_access"] = "本项目以网页呈现 CIE 知识点、国内先修位置、原创教学卡与来源说明。"
    rules["validation"] = "结构验证与界面检查不能证明课程等价、学生掌握或课堂效果。证据状态沿用2026-10-25资料快照，本次发布没有重核全部原件。"
    data = {"schema_version": "2.0-web", "created": source["created"], "published": "2026-11-02",
            "title": "Curriculum Bridge Atlas", "release": "v1.1.1", "subjects": source["subjects"],
            "stages": STAGES, "concepts": concepts, "occurrences": occurrences, "sources": sources,
            "cards": cards, "evidence_rules": rules,
            "counts": {"concepts": len(concepts), "occurrences": len(occurrences), "sources": len(sources), "cards": len(cards)}}
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if OUT_OF_SCOPE.search(rendered):
        raise ValueError("Out-of-scope curriculum reference remains in the website data")
    (ROOT / "data/atlas.json").write_text(rendered, encoding="utf-8")
    print(json.dumps(data["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
