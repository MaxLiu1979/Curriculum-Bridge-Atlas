#!/usr/bin/env python3
"""Build the website preview from curated data and the public author profile."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "data/atlas.json").read_text(encoding="utf-8"))
    author = json.loads((ROOT / "web/author.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", author["email"]):
        raise ValueError("Author email must be a complete public contact address")
    template = (ROOT / "web/index.template.html").read_text(encoding="utf-8")
    placeholders = {"NAME": "name", "ROLE": "role_zh", "TAGLINE": "tagline_zh", "BIO": "bio_zh", "EMAIL": "email", "GITHUB": "github_url", "DISCUSSIONS": "discussions_url"}
    for placeholder, field in placeholders.items():
        template = template.replace("__AUTHOR_" + placeholder + "__", html.escape(author[field], quote=True))
    for key, value in data["counts"].items():
        template = template.replace("__COUNT_" + key.upper() + "__", f"{value:,}")
    embedded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    output = template.replace("__ATLAS_DATA__", embedded)
    if re.search(r"__(?:AUTHOR|COUNT|ATLAS)_[A-Z_]+__", output):
        raise ValueError("Unresolved website template placeholder")
    (ROOT / "index.html").write_text(output, encoding="utf-8")
    print(f"Built CIE website: {len(data['concepts'])} concepts, {len(data['cards'])} teaching cards.")


if __name__ == "__main__":
    main()
