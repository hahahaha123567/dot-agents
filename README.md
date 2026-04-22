# Agents Skills

本仓库维护本机 Codex / 代理可调用的自定义 skills。每个 skill 的主入口位于 `skills/<skill>/SKILL.md`。

| 目录 | Skill 名称 | 功能简介 |
| --- | --- | --- |
| `agent-doc-scaffold` | `agent-doc-scaffold` | 为现有代码仓库或 monorepo 生成、刷新代理指令文档，包括根 `AGENTS.md`、精简 `CLAUDE.md`、`doc/` 索引和可选子模块说明。 |
| `article-tagger` | `article_tagger` | 为文章添加 1-2 个宏观分类标签，用于大致区分文章主题，例如游戏、科技、经济、政治、文化等。 |
| `branch-diff-review` | `branch-diff-review` | 对比当前分支与指定基准分支，生成面向测试同学的代码变更 Review 报告，突出功能变化、风险点和测试建议。 |
| `cursor-usage-csv` | `cursor-usage-csv` | 汇总本地 Cursor 用量 CSV，按模型统计 token，并使用中文万/亿格式输出排序后的用量表。 |
| `hand-drawn-infographic` | `hand-drawn-infographic` | 根据用户内容生成 16:9 手绘卡通风格信息图，提炼关键观点并用涂鸦、图标和简短文字呈现。 |
| `hv-analysis` | `hv-analysis` | 使用横纵分析法系统研究产品、公司、概念、技术或人物，纵向梳理发展历程，横向对比同类对象，最终产出 PDF 研究报告。 |
| `jumpserver-log-debug` | `jumpserver-log-debug` | 通过本机 JumpServer alias 登录目标服务器，检索服务日志、提取 `log_id`，并结合本地代码变更分析线上行为。 |
| `netnewswire-archive` | `netnewswire-archive` | 从 NetNewsWire starred 文章或手动 URL 抓取完整原文，识别来源和宏观标签后归档到 Obsidian。 |
| `resume-analyzer` | `resume-analyzer` | 分析和优化简历/CV，读取 PDF 或 DOCX 后生成交互式 HTML 报告，逐条展示原文、建议改法和修改原因。 |
| `review-staged-commit` | `review-staged-commit` | 审查 staged 与 unstaged tracked Git 变更，确认无明显风险后生成 commit message 并提交。 |
| `weekly-report` | `weekly-report` | 结合用户口述进展和 `~/IdeaProjects/` 下 Git 提交记录，生成结构化中文程序员周报。 |
