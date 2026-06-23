# Agents Skills

本仓库维护本机 Codex / 代理可调用的自定义 skills。每个 skill 的主入口位于 `skills/<skill>/SKILL.md`。

| Skill 名称 | 功能简介 |
| --- | --- |
| `agent-doc-scaffold` | 为现有代码仓库或 monorepo 生成、刷新代理指令文档，包括根 `AGENTS.md`、精简 `CLAUDE.md`、`doc/` 索引和可选子模块说明。 |
| `article_tagger` | 为文章添加 1-2 个宏观分类标签，用于大致区分文章主题，例如游戏、科技、经济、政治、文化等。 |
| `branch-diff-review` | 对比当前分支与指定基准分支，生成面向测试同学的代码变更 Review 报告，突出功能变化、风险点和测试建议。 |
| `cursor-usage-csv` | 汇总本地 Cursor 用量 CSV，按模型统计 token，并使用中文万/亿格式输出排序后的用量表。 |
| `draw-archify` | 生成专业架构图、流程图、时序图、数据流图及生命周期图，输出可导出的独立 HTML 图表。 |
| `draw-crochet-doll-image` | 将指定图片或描述对象转换成温馨钩针玩偶、毛线质感和怀旧毛公仔风格。 |
| `draw-folk-doodle-image` | 将用户提供或描述的图像转化为装饰性民间平面插图，并融入涂鸦元素。 |
| `draw-hand-drawn-infographic` | 根据用户内容生成 16:9 手绘卡通风格信息图，提炼关键观点并用涂鸦、图标和简短文字呈现。 |
| `draw-orange-line-illustration` | 生成纽约客风格极简橙线插画，用于文章配图、封面图、公众号插图、概念插画和 PPT 配图。 |
| `hv-analysis` | 使用横纵分析法系统研究产品、公司、概念、技术或人物，纵向梳理发展历程，横向对比同类对象，最终产出 PDF 研究报告。 |
| `jumpserver-log-debug` | 通过本机 JumpServer alias 登录目标服务器，检索服务日志、提取 `log_id`，并结合本地代码变更分析线上行为。 |
| `article-archive` | 从手动 URL 抓取完整文章，识别来源和内容标签后归档到 Obsidian。 |
| `resume-analyzer` | 分析和优化简历/CV，读取 PDF 或 DOCX 后生成交互式 HTML 报告，逐条展示原文、建议改法和修改原因。 |
| `review-staged-commit` | 审查 staged 与 unstaged tracked Git 变更，确认无明显风险后生成 commit message 并提交。 |
| `weekly-report` | 结合用户口述进展和 `~/IdeaProjects/` 下 Git 提交记录，生成结构化中文程序员周报。 |
