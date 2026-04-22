---
name: review-staged-commit
description: Reviews staged and unstaged tracked git changes for obvious issues, then generates a commit message and commits if safe. When unstaged tracked changes are present, the skill will include them in review and, if they pass, precisely git add the involved tracked files before commit. Commit messages and replies describe the change only—no tool/AI/editor attribution in message body (editor-side options like Cursor "Commit with attribution" are separate). Use when the user asks to "review staged/unstaged code", "帮我看下改动然后顺手提交", "生成 commit message 并提交", or wants an automated review-then-commit workflow in Cursor.
---

# Review staged changes then commit

## 适用场景

- 用户说"我已经 `git add` 了，帮我 review 一下然后 commit"
- 用户说"我改好了还没 add，帮我顺手 review + 提交"
- 用户说"生成 commit message 并提交"
- 用户希望 Cursor 自动化完成 **代码审查（纳入 staged 与 unstaged tracked 变更）→ 自动 add（仅本次变更）→ 生成 commit message → commit**

## 约束（本 Skill 固定行为）

- **默认同时 review staged diff 与 unstaged tracked diff**（`git diff --cached` + `git diff`），不跑编译/测试（用户已选择 diff-only）。
- **若存在 unstaged tracked 变更**：审查通过后，会仅对本次涉及的 tracked 文件执行精确的 `git add <files>`，再与原有 staged 内容一并提交。
- **未跟踪文件默认不自动纳入**：若 `git status` 中存在 `??`，需提示用户确认后才可 `git add`。
- 若发现本次 diff 引入的明确缺陷或高置信阻塞风险：**不提交**，先输出审查结论与修改建议；仅凭猜测或无法定位影响范围的问题不作为阻塞项。
- 严格遵守仓库 Git 安全协议：不改 git config；不做破坏性命令；不跳过 hooks；不 force push。
- **正文不写来源署名**：commit message 与本轮回复只写审查结论与变更说明；不在正文里加工具/模型/编辑器名或「由 AI 生成」类措辞。若要在提交元数据中避免编辑器署名，由用户在 Cursor 等客户端里关闭「Commit with attribution」等选项，与本 skill 分工不同。
- **小改动时避免冗余输出**：若本次仅涉及 1-2 个文件、diff 很短且未发现风险，回复应压缩为 2-4 行或 1 个短段落，只保留审查结论、核心改动、是否已提交和 commit hash；不要机械重复完整模板。

## 工作流（必须按顺序执行）

### Step 0：收集上下文（必须执行）

**并行执行**以下命令（它们相互独立，可在同一批 tool call 中发起）：

```bash
git status --short          # 查看仓库状态（含 untracked 文件）
git diff --cached           # 获取 staged 差异
git log -10 --oneline       # 获取最近提交风格
```

```bash
git diff                    # 获取工作区差异（unstaged tracked）
```

**多仓库工作区处理**：若 workspace 包含多个 git 仓库，需确定目标仓库：
- 若用户通过 `@path` 或上下文明确指定了仓库 → 使用该仓库。
- 若用户未指定 → 依次检查各仓库的 `git status`，仅对有变更的仓库执行后续流程。
- 若多个仓库都有变更 → 询问用户想审查哪个，或逐个处理。

### Step 1：判定是否可提交

1. **选择本次要审查的 diff 源**：
   - 若 `git diff --cached` 与 `git diff` 均非空：以 **staged + unstaged** 为审查源；审查通过后对 unstaged 涉及的 tracked 文件执行 `git add <files>`，再与现有 staged 内容一并提交。
   - 若仅 `git diff --cached` 非空：以 **staged diff** 为审查源；仅提交已暂存内容。
   - 若仅 `git diff` 非空：以 **unstaged diff** 为审查源；审查通过后对涉及文件执行 `git add <files>` 再提交。
   - 若仅存在 **untracked 文件**（`git status` 中 `??` 状态）：提示用户当前有新文件未跟踪，询问是否纳入本次提交。不自动 `git add` untracked 文件。
   - 若 staged、unstaged、untracked 均为空：告知用户"当前没有可审查的变更"，结束流程。

2. **敏感文件/疑似密钥检查**（发现则默认阻止提交，除非用户明确要求）：
   - 文件名命中以下模式：`.env*`、`credentials*`、`id_rsa*`、`*.pem`、`*.p12`、`*.key`、`*.keystore`、`*.jks`、`application-prod*`、`secret*`、`*token*`
   - diff 内容中出现高风险字段：`AKIA`、`secret`、`accessKey`、`accessKeySecret`、`privateKey`、`password`、`token`、`BEGIN PRIVATE KEY`、`BEGIN RSA PRIVATE KEY`、`BEGIN CERTIFICATE`

3. **缺陷判定原则（参考 Codex 官方 review 方法）**
   - 只标记作者知道后大概率会修的明确问题；不要为了完整性输出风格、偏好或泛泛建议。
   - 问题必须是本次 diff 引入或暴露的；不要把已有历史问题当作本次阻塞项。
   - 问题必须离散、可操作，并且能说明触发场景、输入、环境或受影响调用链。
   - 不要依赖未说明的意图假设；如果怀疑会影响其他代码，必须能用 diff 或上下文定位被影响的具体位置。
   - 若变更看起来像作者有意调整，除非能证明会破坏既有行为、兼容性、安全性或可维护性，否则不要标为缺陷。
   - 忽略纯格式、拼写、命名等细枝末节，除非违反项目明确规则或会遮蔽真实含义。
   - 不要停在第一个问题；继续检查并列出所有符合上述标准的问题。

4. **明显错误/高风险变更检查（diff-only 的"明显错误"定义）**
   - **编译级问题的强信号**：明显的语法错误、缺失括号、明显的 import/类名不匹配、删除了被引用的方法签名但无替代等
   - **逻辑级高风险**：空指针风险（新增 `xxx.getYyy().getZzz()` 无判空）、并发/锁相关逻辑被改动但无保护、金额/计费/状态机关键逻辑变更但缺少兼容分支
   - **SQL/持久层风险**：新增全表扫描条件、缺少分片键 `tenant_id`、无索引条件的范围更新/删除等
   - **配置/运维风险**：环境 profile 遗漏（如新增环境但日志/配置未覆盖）、端口/地址硬编码、超时值异常等
   - **可回滚性**：一次提交混入大量无关格式化/重构 + 业务改动（建议拆分）

5. **严重级别与提交决策**
   - `[P0]`：阻断发布、线上运行或核心使用的普遍问题；必须阻止提交。
   - `[P1]`：下个迭代必须修的紧急问题；必须阻止提交。
   - `[P2]`：普通缺陷，作者知道后通常会修；默认阻止提交。
   - `[P3]`：低风险改进或可读性建议；不阻止提交，可在建议项中说明。
   - 敏感文件、疑似密钥、破坏性 SQL、数据丢失风险默认按 `[P0]` 或 `[P1]` 处理。

6. **发现项写法**
   - 每个发现项只描述一个问题，尽量附文件路径和最短可定位行号。
   - 用 1 个短段落说明为什么这是 bug，并明确触发条件或受影响场景。
   - 语气保持事实化，不夸大严重性；不要写空泛的"可能有问题"。
   - 代码片段最多 3 行，只在能直接帮助定位或修复时使用。

7. **大 diff 的分级审查策略**（变更文件 ≥ 5 个或 diff 行数 ≥ 200 行时适用）：
   - 优先审查：业务逻辑代码（Service / Controller / DAO 层）、SQL 变更、配置文件
   - 次要审查：DTO/VO/Entity 字段新增、依赖版本变更
   - 可略过：纯 import 排序、空行/格式化调整
   - 若仅从 diff 无法判断风险（如方法被删除但不确定是否有调用方），使用 Read / Grep 工具查看上下文后再下结论

8. 若发现 `[P0]`、`[P1]` 或 `[P2]` 问题，输出：
   - **阻塞项**（必须修）
   - **建议项**（可选）
   - **建议的下一步**（改哪里、怎么改）
   然后停止流程（不 commit、不自动 add）。

### Step 2：生成 commit message（遵循仓库风格）

1. 先判断仓库近期 commit message 是否明显采用 Conventional Commits（例如 `feat: ...`、`fix(scope): ...`）：
   - 若是：使用 Conventional Commits，类型前缀保持英文（`feat|fix|refactor|perf|docs|test|chore`），**scope 和描述部分使用中文**。
   - 若否：用仓库常见风格（从 `git log -10 --oneline` 归纳），保持简洁。

2. **语言规则**：
   - **普通动词和业务逻辑描述一律使用中文**，不要用英文动词开头（如 guard / skip / add / update / remove），改用对应中文（如 增加 / 跳过 / 新增 / 更新 / 移除）。
   - 仅保留专有名词、类名、方法名、字段名、技术术语等英文原名（如 `accountId`、`NPE`、`accountClient`）。

3. Commit message 内容要求：
   - 标题 1 行：用中文说明"做了什么 + 为何"，避免纯 "update/fixbug"
   - Body 2–6 行：用中文列关键点（对行为变化、兼容性、风险点、回滚点进行说明）
   - 不写长篇背景；不包含敏感信息
   - **标题与 body 为纯变更描述**：不出现工具名、模型名或暗示自动生成的装饰；与客户端是否在 commit 元数据里附加署名无关。

### Step 3：执行 commit（仅提交本次审查通过的内容）

1. **若存在 unstaged tracked diff**：在审查通过后，先对本次 diff 涉及且不含敏感信息的 tracked 文件执行精确的 `git add <files>`，不自动 `git add .`，避免误带入未预期改动。
2. **若仅有 staged diff**：直接提交已暂存内容。
3. 使用 heredoc 传递 message（保证格式稳定）：

```bash
git commit -m "$(cat <<'EOF'
<title>

<body>
EOF
)"
```

4. commit 完成后再 `git status` 校验结果。

### Step 4：异常处理

**commit 被 hook 拒绝或执行失败**：
- 输出完整的错误信息（exit code + stderr）。
- 分析失败原因（lint 不通过、commit-msg 格式校验失败、merge conflict 等）。
- 给出修复建议，但**不自动重试**（避免循环），等待用户确认后再操作。

**commit 成功但 hook 自动修改了文件**（工作区出现新变更）：
- 仅当满足以下条件才允许 `--amend`：
  - commit 是本次流程创建的
  - 变更是 hook 自动生成/格式化且应当纳入同一提交
  - 该 commit 未 push
- 否则创建一个新 commit（除非用户明确要求 amend/force push）。

## 输出模板（审查通过时）

按如下结构输出（中文即可）；**结尾不要加**来源/免责声明（正文职责同上）。

若本次改动很少（例如仅 1-2 个文件、总 diff 很短、无阻塞项），可使用简化输出，不必逐项展开“主要变更点 / 风险点 / Commit message”等字段；但至少应包含：
- 审查结论
- 1 句核心改动说明
- 是否已提交
- commit hash（若已提交）

- **审查源**：staged + unstaged / staged / unstaged
- **Review 结论**：通过 / 有阻塞项
- **主要变更点**：1–3 条
- **风险点**：若无则写"未发现明显风险（基于 diff-only 审查）"
- **Commit message**：展示最终 message（纯变更描述）
- **已执行操作**：`git commit` 成功与否、commit hash
