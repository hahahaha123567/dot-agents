---
name: agent-doc-scaffold
description: 为现有代码仓库或 monorepo 生成或刷新代理指令文档，包括作为唯一共享规范的根 AGENTS.md、仅引用 AGENTS.md 的精简 CLAUDE.md、放在 doc/ 下的代理文档索引，以及可选的子模块 AGENTS.md。适用于需要为项目初始化多代理协作规范、为编码代理补齐仓库级入门文档，或统一 OpenAI / Claude 兼容指令文档结构的场景。
---

# Agent Doc Scaffold

## 概述

先检查目标仓库，再生成一套适合编码代理使用的首版指令文档，包括仓库级和模块级说明。将 `AGENTS.md` 作为唯一共享规范，将 `CLAUDE.md` 保持为精简引用层，并把索引固定生成到 `doc/`。

除非用户明确要求其他语言，否则默认生成中文文档；只有在英文专有名词、文件名、命令名或行业惯用表达更清晰时保留英文。

## 工作流

1. 生成前先检查目标仓库：
   - 读取根目录的 manifest 和 workspace 文件，例如 `package.json`、`pom.xml`、`build.gradle*`、`pyproject.toml`、`go.mod`、`Cargo.toml`、`pnpm-workspace.yaml`、`settings.gradle*` 或 `Makefile`。
   - 读取根目录 `README`，以及已有的代理说明文档。
   - 基于真实仓库判断 build、test、lint、dev 命令，而不是仅凭语言猜测。
   - 判断仓库是否为 monorepo，以及哪些子模块值得拥有各自的 `AGENTS.md`。

2. 运行脚手架脚本：

   ```bash
   python3 /Users/zhangyaoxin/.agents/skills/agent-doc-scaffold/scripts/generate_agent_docs.py /path/to/repo
   ```

   常用参数：

   ```bash
   python3 /Users/zhangyaoxin/.agents/skills/agent-doc-scaffold/scripts/generate_agent_docs.py /path/to/repo --force
   python3 /Users/zhangyaoxin/.agents/skills/agent-doc-scaffold/scripts/generate_agent_docs.py /path/to/repo --no-submodules
   python3 /Users/zhangyaoxin/.agents/skills/agent-doc-scaffold/scripts/generate_agent_docs.py /path/to/repo --module packages/api --module apps/web
   ```

3. 根据仓库事实回看并收紧生成结果：
   - 如果仓库已有明确的包装命令，替换掉泛化的命令建议。
   - 补充代码里看不出的架构边界、部署限制、已知特殊约束。
   - 删除弱约束和重复内容，不要一味把文档写长。

4. 保持输出结构稳定：
   - 根 `AGENTS.md`：所有代理共享的唯一规范。
   - 根 `CLAUDE.md`：只做引用，不复制 `AGENTS.md` 内容。
   - `doc/agent-doc-index.md`：记录代理文档及作用域的索引。
   - 子模块 `AGENTS.md`：仅在局部上下文明显不同的情况下生成增量说明。

## 内容规则

- 共享规则统一写在根 `AGENTS.md`，不要散落到多个顶层文件。
- `CLAUDE.md` 保持简短，并回指 `AGENTS.md`。
- 模块级 `AGENTS.md` 只做增量补充，且作用域仅限其所在子树。
- 优先使用直接、命令式表达，而不是解释性很强的大段 prose。
- 只要已知，就应写入具体命令、路径、约束、校验预期和作用域边界。
- 文件保持简洁；如果根文档开始膨胀，把长内容移到 `doc/` 并加入索引。
- `AGENTS.md` 尽量避免过强的厂商绑定表达；确需厂商特定内容时，放进对应文件。
- 除非用户明确要刷新，否则不要覆盖已有的人写代理文档；仅在确定要替换 starter 时使用 `--force`。

## 脚本行为

- 脚手架脚本会用仓库启发式规则识别 manifests、模块根目录、workspace 布局和可能的命令。
- 默认只在文件不存在时写入；如需覆盖，使用 `--force`。
- 自动识别出的模块只是起点，不是真理；如果仓库布局特殊，应显式传入 `--module`。
- 脚本生成的是可用 starter，生成后仍应结合真实仓库事实进行收紧和修订。

## 资源

- `scripts/generate_agent_docs.py`：向目标仓库写入根级和模块级代理文档。
- `references/agent-doc-best-practices.md`：压缩整理的 OpenAI / Anthropic 公开最佳实践，以及本 skill 遵循的输出约定。

## 完成标准

- 目标仓库包含预期的根级文件和 `doc/agent-doc-index.md`。
- 只有在确实有价值时，才生成模块级 `AGENTS.md`。
- 生成的指令与仓库真实命令和边界足够贴近，使另一个代理无需重新收集同样上下文就能开始工作。
