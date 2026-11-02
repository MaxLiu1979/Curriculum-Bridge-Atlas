# Curriculum Bridge Atlas

## 👉 [点击这里，直接打开可操作的网页版](https://maxliu1979.github.io/Curriculum-Bridge-Atlas/)

打开后按 **选科目 → 点知识点 → 看对应表 → 预览教学卡** 使用。

日常使用请从上方网页入口进入。GitHub 仓库里的 `index.html` 是页面源文件，点开只会显示代码；可操作页面位于上方独立的网址。

**CIE 课程衔接知识图谱｜由 Max Liu 发起与整理**

同一个知识点，在国内初高中和 CIE 中，分别讲到什么程度？转入后还需要补什么？

**[打开网页 →](https://maxliu1979.github.io/Curriculum-Bridge-Atlas/)** · [和 Max Liu 交流](mailto:max_liu1979@outlook.com) · [参与讨论与共建](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/discussions) · [English](README.en.md)

## 关于发起人

**Max Liu｜高中校长 · AI 教师**

我关注课程衔接、教师 AI 应用与教学资源共建。欢迎老师、课程研究者和教育同行来交流，也欢迎一起把这张图谱做得更好。

**邮箱：[max_liu1979@outlook.com](mailto:max_liu1979@outlook.com)** · [GitHub：MaxLiu1979](https://github.com/MaxLiu1979)

![CIE 知识点检索与网页预览](docs/preview.png)

## 在网页里可以做什么

- 中英双语检索 CIE 知识点，比较国内先修位置与 CIE IGCSE、AS / A-Level、Further Mathematics 的要求。
- 点选知识点直接看到衔接对照表；点表中课程位置或关系图节点，可预览要求和证据边界。
- 在线展开原创教学卡，查看诊断任务、教学活动、迁移练习及教师参考答案。
- 在网页中查看来源书目、页码和版本说明。

全部内容通过网页预览。没有证据的早期正文或系统讲解摘要框不显示；保留有依据的具体内容。

## 当前范围

| 内容 | 范围 |
| --- | --- |
| 学科 | 经济、会计、物理、化学、数学、高数、生物、英语 |
| CIE 概念 / 主题组 | 168 |
| 课程位置与证据线索 | 1,375 |
| 来源书目 | 57，限 CIE 与国内教材 |
| 原创教学卡 | 60，网页预览，含教师参考答案 |
| 课程阶段 | 国内初中、国内高中、CIE IGCSE、CIE AS/A-Level、CIE Further |

资料快照为 **2026-10-25**，网页更新于 **2026-11-02**。只展示本库已经建立直接 CIE 课程位置的概念；没有条目不等于该课程没有相关内容。

教材位置、大纲要求、实际授课和学生掌握分别处理。先修关系、补桥顺序与转入判断属于教研建议，不能自动解释为完整课程等价。正文核对状态沿用资料快照，本次网页更新没有重新逐页复核全部原件，也没有验证课堂效果。详见 [方法说明](docs/METHODOLOGY.md) 与 [来源范围](docs/SOURCES.md)。

## 参与完善

欢迎在 [讨论区](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/discussions) 分享使用体验、教学建议和共建想法，也可通过 [Issue](https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/issues) 报告具体问题。修正课程条目时，请提供概念 ID、CIE 课程代码、年份 / 版本和可公开的页码依据。

页面检索在浏览器内执行，没有账号、分析脚本或数据上传功能。作者公开邮箱专用于联系与交流；课程来源中的学生、班级和私人材料不在页面提供。

## 维护网页

```bash
python scripts/build.py
python scripts/validate.py
node --check web/viewer.js
```

`data/atlas.json` 是经过范围筛选的页面数据，`web/author.json` 是作者本人授权公开的联系资料。`scripts/prepare_data.py` 仅供维护者从本机原资料生成 CIE 范围的数据，不上传原文件。

本项目独立整理，AI 辅助形成初始资料与工具，不代表 Cambridge 或相关出版社的认证与背书。软件代码采用 [MIT](LICENSE)；原创注释与教学练习采用 [CC BY 4.0](CONTENT_LICENSE.md)。第三方课程材料权利不变。
