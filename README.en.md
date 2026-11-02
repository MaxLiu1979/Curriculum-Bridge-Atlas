# Curriculum Bridge Atlas

**A CIE curriculum bridge reference, initiated and curated by Max Liu.**

[Open the website](https://maxliu1979.github.io/Curriculum-Bridge-Atlas/) · [Email Max Liu](mailto:max_liu1979@outlook.com) · [Join the discussion](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/discussions) · [中文](README.md)

## Meet the creator

**Max Liu — high school principal and AI teacher**

Interested in curriculum bridging, AI applications for teachers and collaborative teaching resources. Educators and curriculum researchers are welcome to share ideas, report corrections and help improve the atlas.

Contact: **[max_liu1979@outlook.com](mailto:max_liu1979@outlook.com)** · [GitHub profile](https://github.com/MaxLiu1979)

![CIE knowledge-point viewer](docs/preview.png)

## Browse in the website

Search in Chinese or English, compare domestic secondary foundations with CIE IGCSE / AS & A Level / Further Mathematics, inspect relationship nodes and preview original teaching cards and source locators. All content is presented as web previews.

The current scope contains **168 concepts / topic groups, 1,375 curriculum locations, 57 bibliographic records and 60 original teaching cards** across economics, accounting, physics, chemistry, mathematics, further mathematics, biology and English. Only concepts with a direct CIE curriculum location in the existing dataset are included.

The source snapshot is **25 October 2026**; the website was updated on **2 November 2026**. Empty early-evidence summary panels are omitted. Missing evidence does not establish that a curriculum lacks the topic. Textbook positions, syllabus requirements, actual teaching and learner mastery are separate kinds of information. Prerequisite and bridging proposals are editorial teaching suggestions, not complete curriculum-equivalence findings.

Teaching cards include teacher answers. Original source files and personal classroom records are not provided. Structural and interface checks do not establish classroom effectiveness or re-audit every original document. See [methodology](docs/METHODOLOGY.md) and [sources](docs/SOURCES.md).

## Contribute or maintain

Use the [discussion area](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/discussions) for ideas, or [Issues](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/issues) for corrections with a concept ID, CIE course code, edition and publicly shareable locator. See [contribution guidance](CONTRIBUTING.md).

```bash
python scripts/build.py
python scripts/validate.py
node --check web/viewer.js
```

The website has no account, analytics or upload feature. Software: [MIT](LICENSE). Original annotations and exercises: [CC BY 4.0](CONTENT_LICENSE.md). Third-party rights are unaffected. This independent, AI-assisted project has no official endorsement from Cambridge or textbook publishers.
