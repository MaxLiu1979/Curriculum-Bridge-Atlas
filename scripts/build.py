#!/usr/bin/env python3
"""Build the offline viewer, portable CSV exports and Obsidian notes. Stdlib only."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plain(value):
    if value is None:
        return "未确定"
    if isinstance(value, list):
        return "\n".join("- " + plain(item) for item in value)
    if isinstance(value, dict):
        return "\n\n".join(f"**{key}**：{plain(item)}" for key, item in value.items())
    return str(value)


def note(row, title, body):
    front = "---\nid: " + json.dumps(row["id"], ensure_ascii=False) + "\n---\n\n"
    write(row["note"], front + "# " + title.strip() + "\n\n" + body + "\n")


def wiki(row, label=None):
    return "[[" + row["note"].removeprefix("vault/").removesuffix(".md") + "|" + (label or row.get("title_zh", row.get("title", row["id"]))) + "]]"


def csv_export(path, rows):
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with (ROOT / path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main():
    data = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "exports/graph.json").read_text(encoding="utf-8"))
    embedded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    template = (ROOT / "web/index.template.html").read_text(encoding="utf-8")
    write("index.html", template.replace("__ATLAS_DATA__", embedded))
    cm = {row["id"]: row for row in data["concepts"]}
    om = {row["id"]: row for row in data["occurrences"]}
    sm = {row["id"]: row for row in data["sources"]}
    for c in data["concepts"]:
        body = c["title_en"] + "\n\n" + c["definition"] + "\n\n"
        body += "**解释范围**：" + c["definition_status"] + "\n\n"
        body += "**衔接边界**：" + c["relation_warning"] + "\n\n"
        body += "## 先修关系（教研建议）\n\n" + ("\n".join("- " + wiki(cm[i]) for i in c["prerequisite_ids"] if i in cm) or "尚未列出。") + "\n\n"
        body += "## 分阶段课程位置\n\n"
        for stage in data["stages"]:
            rows = [om[i] for i in c["occurrence_ids"] if om[i]["stage"] == stage]
            body += "### " + stage + "\n\n"
            body += ("\n".join("- " + wiki(o, o["position_label"]) + " — " + o["relation"] for o in rows) or "本库未建立直接条目；不能推断课程没有该内容。") + "\n\n"
        cards = [r for r in data["cards"] if c["id"] in r["concept_ids"]]
        body += "## 教学卡\n\n" + ("\n".join("- " + wiki(r) for r in cards) or "暂无挂接教学卡。")
        body += "\n\n## 实际授课\n\n公开版不收集或附带个人、班级或实际授课记录，不能由课程位置推断已教或掌握。"
        note(c, c["title_zh"], body)
    for o in data["occurrences"]:
        fields = [("阶段", o["stage"]), ("课程", o["course"]), ("位置", o["position_label"]),
                  ("课程代码", o["code"]), ("关系", o["relation"]), ("要求摘要", o["depth_summary"]),
                  ("可观察要求", o["expected_outputs"]), ("补桥与限制", o["gap"]),
                  ("证据状态（资料快照）", o["evidence_status"]), ("版次说明", o.get("version_note", "以所查原件为准")),
                  ("深度类别", o["depth_band"]), ("时间口径", o["teaching_position_status"])]
        body = "\n\n".join(f"**{key}**：{plain(value)}" for key, value in fields)
        if o.get("week_in_plan"):
            body += "\n\n**示例计划周次**：" + plain(o["week_in_plan"]) + "\n\n" + plain(o.get("timing_status"))
        body += "\n\n## 来源定位\n\n"
        if o["source_id"] in sm:
            body += wiki(sm[o["source_id"]]) + "；PDF 物理页：" + plain(o["pdf_pages"])
        else:
            body += "待补原件定位；当前仅作为教研线索，不作为已核原文结论。"
        body += "\n\n原件未随库分发。页码是对应快照的定位，不能套用到其他版次。\n\n## 关联概念\n\n" + "\n".join("- " + wiki(cm[i]) for i in o["concept_ids"])
        note(o, o["title"], body)
    for s in data["sources"]:
        body = f"**类型**：{s['kind']}\n\n**SHA-256**：`{s['sha256']}`\n\n**版次说明**：{s['version_note'] or '以书名及对应原件为准；无补充版次认定。'}\n\n{s['access_note']}"
        if s["url"]:
            body += f"\n\n[原索引记录的公开官方链接]({s['url']})（本次未逐个重核链接或内容）。"
        body += f"\n\n[课程机构 / 教材平台入口]({s['official_entry']})"
        note(s, s["title"], body)
    for r in data["cards"]:
        labels = {"target_course": "接收课程", "target_course_status": "接收课程范围", "target_topics": "主题定位", "teaching_focus": "教学要点", "prerequisites": "先修", "diagnostic_task": "诊断任务", "diagnostic_solution": "诊断参考答案", "common_misconception": "常见误区", "teaching_activity": "教学活动", "practice_task": "迁移练习", "practice_solution": "练习参考答案", "exit_evidence": "退出证据", "as_a2_extension": "AS / A-Level 升级建议", "board_bridges": "考试局接续建议", "transfer_rules": "转入判断建议", "data_notice": "示例数据说明"}
        body = "原创教学练习，非官方试题；含教师参考答案。单次诊断不能替代整科评估。\n\n"
        body += "\n\n".join("## " + labels.get(key, key) + "\n\n" + plain(value) for key, value in r["data"].items() if key not in ("concept_id", "subject", "title"))
        body += "\n\n## 关联概念\n\n" + "\n".join("- " + wiki(cm[i]) for i in r["concept_ids"])
        note(r, r["card_id"] + " " + r["title"], body)
    for subject in data["subjects"]:
        concepts = [c for c in data["concepts"] if subject in c.get("subjects", [c["subject"]])]
        write(f"vault/subjects/{subject}.md", "# " + subject + "\n\n[[" + subject + "知识网络.canvas|打开概念网络]]\n\n" + "\n".join("- " + wiki(c) for c in concepts) + "\n")
        nodes = [{"id": c["id"], "type": "file", "file": c["note"].removeprefix("vault/"), "x": (i % 5) * 320, "y": (i // 5) * 150, "width": 280, "height": 100} for i, c in enumerate(concepts)]
        ids = {c["id"] for c in concepts}
        edges = [{"id": e["id"], "fromNode": e["source"], "toNode": e["target"], "label": "先修建议"} for e in graph["edges"] if e["relation"] == "requires" and e["source"] in ids and e["target"] in ids]
        write(f"vault/{subject}知识网络.canvas", json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2) + "\n")
    write("vault/Home.md", "# Curriculum Bridge Atlas\n\n课程衔接知识图谱\n\n资料快照：2026-10-25；公开版：2026-11-02。\n\n" + "\n".join(f"- [[subjects/{s}|{s}]]" for s in data["subjects"]) + "\n\n## 使用口径\n\n" + "\n\n".join(data["evidence_rules"].values()) + "\n\n完整交互检索请打开仓库根目录的 index.html。\n")
    csv_export("exports/nodes.csv", graph["nodes"])
    csv_export("exports/edges.csv", graph["edges"])
    csv_export("exports/sources.csv", data["sources"])
    write(".nojekyll", "")
    print(f"Built viewer, {len(graph['nodes'])} graph nodes, {len(graph['edges'])} edges and portable notes.")


if __name__ == "__main__":
    main()
