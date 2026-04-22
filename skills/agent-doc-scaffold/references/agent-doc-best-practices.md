# Agent Doc Best Practices

这份说明压缩整理了驱动该 skill 的方法论，以及它遵循的输出约定。

## 来源归纳的原则

### OpenAI

- OpenAI 在 “How OpenAI uses Codex” 中建议在仓库内维护 `AGENTS.md`，用来沉淀命名约定、业务语义、已知特殊点、隐式依赖等持续性上下文。
- OpenAI 的 Docs MCP 文档指出，`AGENTS.md` 是告知代理何时应优先使用特定 MCP 服务或文档来源的可靠位置。
- OpenAI 的相关指导也强调：提示词越接近真实工程任务越好，文件路径、组件名、diff、文档片段和预期范围都能让代理行为更稳定。

截至 2026-04-20 使用的主要公开来源：
- https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf
- https://developers.openai.com/learn/docs-mcp

### Anthropic

- Anthropic 将 `CLAUDE.md` 定义为仓库级指令文件，用来描述项目结构、常用命令和协作方式。
- Anthropic 近期关于大代码库的实践建议使用分层指令文件：根级通用规则，加上必要时更具体的嵌套文件。
- Anthropic 明确建议这些文件应保持简短、直接，并像活文档一样持续维护。
- Anthropic 的提示词指导偏好清晰明确的指令、在顺序重要时给出步骤顺序，以及简洁的任务 framing，而不是含糊或过强语气的表述。

截至 2026-04-20 使用的主要公开来源：
- https://resources.anthropic.com/hubfs/Claude%20Code%20Advanced%20Patterns_%20Subagents%2C%20MCP%2C%20and%20Scaling%20to%20Real%20Codebases.pdf
- https://resources.anthropic.com/hubfs/Scaling%20agentic%20coding%20across%20your%20organization.pdf?hsLang=en
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## 实践层面的综合结论

在生成或修订输出时，使用下面这些规则：

1. 让 `AGENTS.md` 成为唯一共享规范文件。
2. 让 `CLAUDE.md` 保持精简，并回指 `AGENTS.md`，不要重复共享规则。
3. 将索引放到 `doc/` 下，方便人和代理快速定位这些文档。
4. 仅在某个子树确实有不同命令、架构边界或校验规则时，才添加子级 `AGENTS.md`。
5. `AGENTS.md` 的措辞尽量保持厂商中立，让多种代理都能遵循。
6. 使用直接、可操作的表达：先看什么、避免什么、跑什么命令、如何验证。
7. 优先写具体事实，而不是空泛政策。命令、路径、边界和隐性坑点价值最高。
8. 文档要足够紧凑，加载它们应提升上下文质量，而不是挤占上下文窗口。
9. 若无特殊兼容性要求，生成文档时优先使用中文；文件名、命令、技术栈名、工具名和必要专有名词保留英文。

## 本 Skill 的输出约定

默认生成这些文件：

- `AGENTS.md`
- `CLAUDE.md`
- `doc/agent-doc-index.md`
- Optional child `AGENTS.md` files for detected or user-specified modules

遵循这些结构规则：

- 根 `AGENTS.md` 包含仓库级规则、命令提示、作用域解析、安全要求和完成检查项。
- 根 `CLAUDE.md` 告诉 Claude 兼容代理先读 `AGENTS.md`，并把子级 `AGENTS.md` 当作额外的局部规范。
- 索引文档列出生成的文件、它们的作用域，以及支撑这些输出的仓库事实。
- 子级 `AGENTS.md` 是对根文件的扩展，不重复整套仓库规范。

## 哪些情况下需要在脚手架生成后继续收紧

出现以下任一情况时，生成的 starter 都不应被视为最终版本：

- 仓库使用了 `make`、`just`、`task`、Bazel、Pants、Nx、Turborepo 或自定义脚本，而脚手架只能部分识别。
- 仓库存在部署、迁移、安全或数据治理规则，而这些规则无法从代码布局直接看出来。
- 模块拓扑比较特殊，导致自动模块识别漏掉重要边界。
- 仓库里已有质量更高的局部约定文档，应合并其意图，而不是直接覆盖。
