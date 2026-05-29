---
name: hltv-falcons-next
description: 查询 Team Falcons CS2（HLTV team 11283）已确认的下一个赛事和下一场具体比赛，包括已确认对手战队信息、双方 5 名现役队员的近 3 个月 HLTV stats Rating，并分别按 Rating 从高到低排列。适用于用户询问 Falcons、Falcons CS2、Falcons 战队、Team Falcons 下一项赛事、下一场比赛
user-invocable: true
---

# HLTV Falcons 下一场信息查询

## 核心规则

每次都必须使用当前来源。Falcons 的赛程、对手和阵容变化频繁，不要凭记忆回答。以 HLTV 作为主要来源，并在最终回答中附上来源链接。

## 来源 URL

- 比赛列表: `https://www.hltv.org/team/11283/falcons#tab-matchesBox`
- 赛事列表: `https://www.hltv.org/team/11283/falcons#tab-eventsBox`
- 战队主页: `https://www.hltv.org/team/11283/falcons`

按需从 HLTV 链接打开比赛、赛事、对手战队和选手页面。如果 HLTV 因 Cloudflare 阻止直接 HTTP 抓取，使用浏览器/搜索访问，或要求用户提供保存后的页面 HTML，不要猜测。

## 工作流程

1. 确认信息时效:
   - 浏览 HLTV 比赛列表和赛事列表标签页 URL。
   - 记录当前查询日期和时区。
   - 忽略模型缓存知识和旧文章，除非它们直接链接到同一批当前 HLTV 页面。

2. 找到下一个已确认赛事:
   - 使用赛事标签页中的 upcoming/attending events 列表。
   - 选择明确列出 Falcons 参赛的最早未来赛事。
   - 提取赛事名称、日期范围、地点和赛事 URL。
   - 如果没有列出未来赛事，说明 HLTV 当前没有显示已确认的下一项赛事。

3. 找到下一场已确认比赛:
   - 使用比赛标签页中的 upcoming matches 列表。
   - 选择 Falcons 最早的一场已排期比赛。
   - 只有当 HLTV 显示对手战队名称/链接时，才把对手视为已确认。如果条目显示 TBD、未公布，或只显示赛程占位，说明下一场对手尚未确认。
   - 提取比赛日期/时间、所属赛事、赛制（如页面显示）、对手，以及 HLTV 直达比赛 URL。

4. 在下一场比赛对手已确认时收集阵容详情:
   - 如可用，打开 Falcons 比赛页，并优先使用其中的 Lineups 区块作为双方 5 名现役选手的来源。
   - 如果比赛页不显示阵容，打开 Falcons 战队页和对手战队页，使用各自页面中的 active players/lineup 区块。
   - 打开比赛页或比赛列表中链接到的对手战队页面。
   - 内部使用已确认的 5 名现役选手进行 stats 查询。
   - 最终回答中不要单独输出“双方五人名单”表格。
   - 如果任一方的 5 名现役选手无法从 HLTV 确认，明确说明缺失的是哪一部分，不要凭记忆补全。

5. 收集选手 Rating 数据:
   - 在确认双方各 5 名选手后，使用子代理查询 10 名选手的 Rating。除非子代理不可用，否则主代理不要串行查询全部 10 个选手 Rating 页面。
   - 启动子代理前，主代理必须准备一份紧凑查询列表，包含每名选手的战队、昵称、选手主页 URL、形如 `https://www.hltv.org/stats/players/<playerId>/<slug>` 的 stats URL，以及共享的近 3 个月日期窗口。
   - 尽可能使用 3 个月日期筛选: `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`，其中 `endDate` 是查询日期，`startDate` 是其前 90 天。
   - 优先并行使用两个子代理: 一个负责 5 名 Falcons 选手，另一个负责 5 名对手选手。如果子代理数量限制或浏览问题导致不可行，仅在必要时拆成更小批次。
   - 每个子代理只能查询分配给自己的选手，打开分配的 HLTV stats URL，或在必要时使用当前 HLTV 选手页作为后备，并返回结构化结果，包含 `team`、`nickname`、`rating`、`rating_version`、`stats_url`、`source_url`，以及不可用时的 `error`。
   - 每个子代理必须从 stats 页面抓取页面显示的 Rating 值。HLTV 显示 Rating 3.0 时优先使用 Rating 3.0；否则使用 HLTV 显示的 Rating 版本，并清楚标注。
   - 子代理不得使用记忆、旧文章或无关选手简介摘要作为替代。如果 stats 页面无法读取，子代理必须准确报告哪个选手失败以及失败原因。
   - 主代理负责合并子代理输出，检查 10 名分配选手是否都已尝试查询；如有重复或冲突条目，重新打开相关 HLTV 来源解决；并保留所有 Rating 缺失警告。
   - Falcons 选手按 Rating 降序排列，对手选手也按 Rating 独立降序排列。

6. 输出简洁回答:
   - `查询时间`: 绝对日期/时间和时区。
   - `下一个已确认赛事`: 赛事名称、日期、关键详情、HLTV URL。
   - `下一场已确认比赛`: 比赛日期/时间、Falcons vs 对手、所属赛事、赛制（如可用），以及清楚标注的 `HLTV 比赛链接` 和直达比赛 URL。
   - `对手信息`: 战队名称、国家/排名（如页面显示）、HLTV URL。
   - `近 3 个月 Rating 排名`: 使用适合终端阅读的纯文本对齐表格，放在 fenced `text` 代码块中，不使用 Markdown 表格。Falcons 选手按 Rating 降序，对手选手按 Rating 降序，分成两个区块或左右并列表达。包含排名、选手和 Rating。不要包含差值、更高 Rating 选手或直接对位表述。
   - `来源`: 使用过的 HLTV 直达链接。
   - 说明因对手缺失、阵容不完整、stats 页面不可用或 HLTV 访问限制导致的任何不确定性。

## 辅助脚本

当可以直接抓取，或已经从浏览器保存页面 HTML 时，使用 `scripts/falcons_next_hltv.py` 解析 HLTV HTML:

```bash
python3 scripts/falcons_next_hltv.py --fetch
python3 scripts/falcons_next_hltv.py --html falcons.html --opponent-html opponent.html --json
python3 scripts/falcons_next_hltv.py --fetch --match-url https://www.hltv.org/matches/2394219/falcons-vs-legacy-cs-asia-championships-2026 --opponent-url https://www.hltv.org/team/12468/legacy --fetch-player-stats --json
python3 scripts/falcons_next_hltv.py --html falcons.html --match-html match.html --opponent-html opponent.html --falcons-stats-html-dir falcons_stats --opponent-stats-html-dir opponent_stats --json
python3 scripts/falcons_next_hltv.py --self-test
```

该脚本是解析器/辅助工具，不是 Cloudflare 绕过工具，也不是子代理编排器。可在有用时用它识别赛事、比赛、阵容、stats URL 和已保存的 HTML 数据；但 10 名选手的实时 Rating 查询仍应按第 5 步交给子代理。
如果脚本报告 Cloudflare challenge，继续使用基于浏览器的访问或已保存 HTML。
使用已保存的 stats HTML 时，文件名使用 `<playerId>.html`、`<playerId>-<slug>.html`、`<slug>.html` 或 `<nickname>.html`；例如 `15698.html`、`15698-dumau.html`、`dumau.html`。

## 验证

最终回答前，检查每个日期相对于查询时间都是未来日期；所选赛事和比赛是 HLTV 上可见的最早已确认条目；双方阵容来自当前 HLTV 比赛/战队/选手页面；除非不可用，已使用子代理查询 10 名已确认选手的当前 HLTV stats 页面，并带上近 3 个月日期范围；每队选手都按 Rating 降序排列，且没有逐位置比较。
