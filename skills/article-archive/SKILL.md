---
name: article-archive
description: 从手动 URL 抓取完整原文，归档到 Obsidian
user-invocable: true
---

## 功能

1. 接受手动输入的一个或多个 URL
2. 抓取完整原文（使用 curl + 代理）
3. 解析文章内容
4. 归档到 Obsidian

## 网络代理

端口：`socks5://127.0.0.1:7897`

## 目标文件格式

**文件位置：** `/Users/zhangyaoxin/obsidian/文章/`

**文件名：** `YYYY-MM-DD 文章标题.md`

**默认文件内容格式：**
```markdown
[文章标题](原文链接)

#来源类型

#内容标签1 #内容标签2

文章正文
```

**带原始来源的存档页格式：**
```markdown
[文章标题](存档页链接)

#来源类型

#内容标签1 #内容标签2

原始来源：[原始来源名](原始来源链接)

文章正文
```

**无可用链接时的兼容格式：**
```markdown
#来源类型

#内容标签1 #内容标签2

文章正文
```

格式要求：
- 新归档默认使用“链接行 → 空行 → 来源标签行 → 空行 → 内容标签行 → 空行 → 正文”
- 第一行链接使用 Markdown 格式 `[标题](URL)`，标题优先使用原文标题，不为了文件名而删减来源前缀
- 来源标签通常只写一个，表示文章来源或平台
- 内容标签写 1-2 个，表示文章主题，优先从“内容标签”清单中选择；若清单和文章主题明显不匹配，可新增更合适且可复用的内容标签并同步更新本 skill
- 正文从原文第一段开始，不额外添加标题重复行，除非原文正文自身包含该标题
- 保留原文已有的 Markdown 标题、引用、列表、图片和正文链接
- 不添加 YAML front matter
- 不添加抓取时间、归档时间、作者说明、摘要、AI 说明或无来源的备注
- 文件名标题可比链接标题更短，但不能改变文章含义

目录中存在少量历史文件使用“来源标签在第一行”或缺少来源标签的旧格式；新归档按默认格式写，不主动批量改旧文件。

## 来源类型识别

根据 URL 或抓取内容判断，优先使用目录中已有的标签写法：
- `weibo.com` → #微博
- `m.weibo.cn` → #微博
- `mp.weixin.qq.com` → #微信公众号
- `chinadigitaltimes.net/chinese/*.html` 且 `CDT 档案卡` 的 `来源` 链接为 `mp.weixin.qq.com` → #微信公众号
- `chinadigitaltimes.net/chinese/*.html` 且正文或档案卡包含 `微信公众号` / `微信公号` / `微信号` → #微信公众号
- `chinadigitaltimes.net/chinese/*.html` 且标题含 `【404文库】` 或页面为中国数字时代转载存档 → 优先按档案卡原始来源判断；多数归档为 #微信公众号
- `chinadigitaltimes.net/chinese/*.html` 且无法识别原始平台 → 根据档案卡来源或正文判断；仍无法判断时用具体来源名，不默认用 #博客
- `nytimes.com` / `cn.nytimes.com` → #nytimes
- `wsj.com` / `cn.wsj.com` → #WSJ
- `ft.com` → #金融时报
- `bbc.com` → #BBC
- `cnn.com` → #CNN
- `economist.com` → #经济学人
- `theguardian.com` → #卫报
- `zhihu.com` → #知乎
- `reddit.com` → #Reddit
- `nga.178.com` / `bbs.nga.cn` → #NGA
- `v2ex.com` → #v2ex
- `matters.news` / `matters.town` → #matters
- `github.com` / `gist.github.com` → #github
- `x.com` / `twitter.com` → #X
- `program-think.blogspot.com` → #编程随想
- URL 或标题包含 `编程随想` → #编程随想
- URL 包含 `telegra.ph` 且标题或正文显示 `WSJ` / `Wall Street Journal` → #WSJ
- URL 包含 `telegra.ph` 且标题或正文显示 `Economist` / `经济学人` → #经济学人
- 包含 "微信公众号" → #微信公众号
- 其他 → #博客

## 高频来源判断优先级

根据 `/Users/zhangyaoxin/obsidian/文章/` 现有文章前 10 行统计，归档时优先识别这些高频来源：

1. #微信公众号：`mp.weixin.qq.com` 原文；中国数字时代 `【404文库】` / 中文存档页中档案卡来源为微信；正文或档案卡出现微信公众号、微信公号、微信号
2. #编程随想：`program-think.blogspot.com` 或标题含“编程随想”
3. #nytimes：`nytimes.com`、`cn.nytimes.com`
4. #Reddit：`reddit.com`
5. #NGA：`nga.178.com`、`bbs.nga.cn`
6. #WSJ：`wsj.com`、`cn.wsj.com`，或 `telegra.ph` 镜像但标题/正文显示 WSJ
7. #v2ex：`v2ex.com`
8. #BBC：`bbc.com`
9. #经济学人：`economist.com` 或 `telegra.ph` 镜像但标题/正文显示经济学人 / Economist
10. #知乎：`zhihu.com`

## 特殊 URL 处理

### 微博 URL 转换
- 输入：`https://weibo.com/1401527553/Qd0InF4EQ`
- 提取末尾 ID：`Qd0InF4EQ`
- 归档链接优先规范化为：`https://m.weibo.cn/detail/Qd0InF4EQ`
- 抓取时不直接用 `curl` 访问移动版网页或接口；移动版只作为本机 Chrome 打开和截图/OCR 的优先页面，因为网页元素较少、正文区域更清晰

### 微博正文与转发链抓取

处理目标：
- 微博归档必须抓取微博正文、作者、发布时间、可见图片/视频说明和正文链接
- 如果是转发微博，必须获取从原文到当前微博的完整转发链，不只归档最外层转发语
- 转发链正文按时间/层级从原文到外层转发排列，保留每一层作者、发布时间和正文
- 如果某一层因删除、权限或不可见无法展开，正文中明确记录该层不可见，不臆造内容

优先流程：
1. 从 URL 末尾提取微博 ID，例如 `https://weibo.com/1401527553/PiyaLiFkN` 提取 `PiyaLiFkN`
2. 先查询本机 NetNewsWire 缓存，避免重复走浏览器截图
3. NetNewsWire 缓存未命中或内容不完整时，使用本机 Chrome 打开 `https://m.weibo.cn/detail/PiyaLiFkN`，优先从移动版截图/OCR 获取正文
4. 移动版 Chrome 页面不可用、内容缺失或无法展开转发链时，再用本机 Chrome 打开桌面版原链接读取
5. 如果 Chrome 已登录但页面无法通过命令行抓取，使用窗口截图确认可见内容
6. 对转发微博继续点开/展开被转发微博，逐层追到最早原文，再按“原文 → 转发 1 → 转发 2 → 当前微博”整理

微博抓取限制：
- 不再尝试用 `curl` 直接访问 `m.weibo.cn/detail/{id}` 网页
- 不再尝试用 `curl` 直接访问 `m.weibo.cn/statuses/show?id={id}` 接口
- 微博页面读取优先依赖本机 Chrome 登录态、Chrome DOM 读取、窗口截图和 OCR
- 移动版页面仍可作为 Chrome 打开目标，优先用于截图，因为页面元素较少、OCR 更稳定

NetNewsWire 微博缓存：
- 本机 NetNewsWire RSS 缓存固定路径：
  `/Users/zhangyaoxin/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3`
- 当需要归档微博时，优先在该 SQLite 中按原始微博 URL、移动版 URL 或微博 ID 查询
- 常用字段：`externalURL` 为原文链接，`contentHTML` 为缓存正文，`datePublished` 为 Unix 时间戳
- 命中后用 `contentHTML` 提取正文，用 `datePublished` 转换发布时间；仍需检查是否为转发微博以及缓存内容是否包含完整转发链

按 URL 查询缓存：
```bash
sqlite3 "/Users/zhangyaoxin/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3" \
  "SELECT articleID, externalURL, datetime(datePublished, 'unixepoch', 'localtime'), contentHTML
   FROM articles
   WHERE externalURL = 'https://weibo.com/1401527553/PiyaLiFkN'
      OR externalURL = 'https://m.weibo.cn/detail/PiyaLiFkN'
      OR externalURL LIKE '%PiyaLiFkN%'
   ORDER BY datePublished DESC
   LIMIT 5;"
```

按关键词或作者补查缓存：
```bash
sqlite3 "/Users/zhangyaoxin/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3" \
  "SELECT articleID, externalURL, datetime(datePublished, 'unixepoch', 'localtime'), substr(contentHTML, 1, 2000)
   FROM articles
   WHERE contentHTML LIKE '%tombkeeper%'
      OR contentHTML LIKE '%微博正文关键词%'
   ORDER BY datePublished DESC
   LIMIT 20;"
```

NetNewsWire 命中后的整理要求：
- `contentHTML` 可能包含 HTML 标签，归档前要转换为纯 Markdown 或可读文本
- 如果 `externalURL` 是桌面版微博链接，归档链接仍按微博规则优先规范化为 `https://m.weibo.cn/detail/{mid}`
- `datePublished` 使用本地时区转换后作为微博发布时间；例如可用 `datetime(datePublished, 'unixepoch', 'localtime')`
- 如果缓存只有当前层转发语，仍要继续用 Chrome 移动版页面、Chrome 桌面版页面或截图/OCR 补齐完整转发链

本机 Chrome 打开命令：
```bash
osascript <<'APPLESCRIPT'
tell application "Google Chrome"
  if (count of windows) = 0 then make new window
  set bounds of front window to {80, 80, 1500, 1050}
  set URL of active tab of front window to "https://m.weibo.cn/detail/PiyaLiFkN"
  delay 6
  return {URL of active tab of front window, title of active tab of front window, bounds of front window}
end tell
APPLESCRIPT
```

如果移动版 Chrome 页面内容不完整，再打开桌面版原链接：
```bash
osascript <<'APPLESCRIPT'
tell application "Google Chrome"
  if (count of windows) = 0 then make new window
  set bounds of front window to {80, 80, 1500, 1050}
  set URL of active tab of front window to "https://weibo.com/1401527553/PiyaLiFkN"
  delay 6
  return {URL of active tab of front window, title of active tab of front window, bounds of front window}
end tell
APPLESCRIPT
```

Chrome DOM 读取：
```bash
osascript <<'APPLESCRIPT'
tell application "Google Chrome"
  set pageUrl to URL of active tab of front window
  set pageTitle to title of active tab of front window
  set pageText to execute active tab of front window javascript "document.body ? document.body.innerText.slice(0, 20000) : ''"
  return pageUrl & linefeed & pageTitle & linefeed & "---TEXT---" & linefeed & pageText
end tell
APPLESCRIPT
```

注意：
- 如果 Chrome 返回“通过 AppleScript 执行 JavaScript 的功能已关闭”，需要用户在 Chrome 菜单中启用“查看 → 开发者 → 允许 Apple 事件中的 JavaScript”，并确认启用的是当前正在使用的 Chrome 实例
- 不在对话或归档正文中输出 cookie、token、登录态、浏览器扩展信息或其他敏感数据
- 如果误用公开 `curl` 返回 `Sina Visitor System`，说明微博访客系统拦截了未登录请求；微博归档应改用 NetNewsWire 缓存或本机 Chrome 登录态查看页面

窗口截图兜底：
```bash
cat > /tmp/list_windows.swift <<'SWIFT'
import Foundation
import CoreGraphics
if let list = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as? [[String: Any]] {
    for w in list {
        let owner = w[kCGWindowOwnerName as String] as? String ?? ""
        if owner == "Google Chrome" {
            let id = w[kCGWindowNumber as String] ?? ""
            let name = w[kCGWindowName as String] ?? ""
            let layer = w[kCGWindowLayer as String] ?? ""
            let bounds = w[kCGWindowBounds as String] ?? ""
            print("\(id)\t\(layer)\t\(name)\t\(bounds)")
        }
    }
}
SWIFT
swift /tmp/list_windows.swift
screencapture -x -l WINDOW_ID /tmp/weibo-window.png
```

微博归档正文推荐结构：
```markdown
作者：微博作者
时间：YYYY-MM-DD HH:mm

微博正文

## 转发链

### 原文｜原文作者｜YYYY-MM-DD HH:mm

原文正文

### 转发 1｜转发作者｜YYYY-MM-DD HH:mm

转发正文

### 当前微博｜当前作者｜YYYY-MM-DD HH:mm

当前微博正文
```

整理要求：
- 单条原创微博没有转发链时，不强行增加 `## 转发链`
- 转发微博必须包含 `## 转发链`
- 转发链中同一层的图片、视频、长文链接、话题和 @ 用户要保留或用简短文字说明
- 转发链不能只写“转发了某人微博”，必须尽量展开被转发内容
- 如果页面只显示摘要，需要点击“展开”“全文”“查看原微博”或打开对应层级链接继续获取

### tombkeeper 专题微博归档

适用目录：
- `/Users/zhangyaoxin/obsidian/文章/tombkeeper/`

适用对象：
- `tombkeeper` / `t0mbkeeper` 发布或转发、且用户明确要求归入 tombkeeper 专题的微博
- 该专题是作者专题子目录，不沿用 `/Users/zhangyaoxin/obsidian/文章/` 根目录的新文章默认格式

与 `/Users/zhangyaoxin/obsidian/文章/` 根目录不同的部分：
- 文件位置固定为 `/Users/zhangyaoxin/obsidian/文章/tombkeeper/`
- 文件名仍用 `YYYY-MM-DD 文章标题.md`，日期取微博发布时间，标题从微博正文提炼，不能改变原意
- 第一行固定使用 `[微博](微博链接)`，链接优先用 `https://m.weibo.cn/detail/{mid}`；能取得数字 `mid` 时用数字 `mid`，否则用原始微博 ID
- 来源标签与根目录同步，使用 `#微博`
- 内容标签与根目录同步，从“内容标签”清单中选择 1-2 个，放在 `#微博` 下方
- 不添加作者、归档时间、抓取说明、摘要或 YAML front matter
- 内容标签后空一行直接进入微博正文
- 正文保留微博原文换行；微博原文中的空行可用 Markdown 硬换行或自然段保留
- 如有补充来源、引用资料或外部链接，在正文后用 `---` 分隔，再放 Markdown 链接或摘录

专题格式：
```markdown
[微博](https://m.weibo.cn/detail/数字mid)

#微博

#内容标签1 #内容标签2

微博正文

---

[补充资料标题](补充资料链接)

补充摘录或说明
```

从原文到本地归档流程：
1. 先查 NetNewsWire 缓存；缓存未命中时用本机 Chrome 打开 `m.weibo.cn/detail/{id}` 确认全文，必要时截图/OCR，不直接用 `curl` 访问移动版网页或接口
2. 记录作者是否为 `tombkeeper` / `t0mbkeeper`，确认该微博应进入 tombkeeper 专题目录
3. 读取发布时间，转换为文件名前缀 `YYYY-MM-DD`
4. 从微博正文提炼短标题；如果正文第一句足够明确，可直接作为文件名标题
5. 将原始 URL 规范化为 `https://m.weibo.cn/detail/{mid}`，优先保留数字 `mid`
6. 按专题格式写入 `/Users/zhangyaoxin/obsidian/文章/tombkeeper/YYYY-MM-DD 标题.md`
7. 根据正文主题从“内容标签”清单中选择 1-2 个标签
8. 写入后检查第一行链接、`#微博` 标签、内容标签、正文起始位置和转发链完整性

转发微博处理：
- 如果 tombkeeper 微博是转发，仍必须先获取从原文到当前微博的完整转发链
- 专题正文可以按“原文 → 转发 1 → 当前微博”顺序整理，但仍保持 tombkeeper 专题的简洁格式：使用 `#微博` 和 1-2 个内容标签，不添加作者说明、摘要或归档说明
- 每层至少保留作者、时间和正文；不可见层明确写“该层微博不可见/已删除/权限受限”
- 如果当前微博只是评论转发，文件名标题优先从当前 tombkeeper 转发语或整条转发链主题中提炼

### 中国数字时代微信公众号存档页

适用 URL 示例：
- `https://chinadigitaltimes.net/chinese/726746.html`

处理目标：
- 这类页面是中国数字时代对原始文章的存档，若 `CDT 档案卡` 中的 `来源` 指向 `mp.weixin.qq.com`，归档时来源类型按 `#微信公众号`，不要误判为 `#博客`
- Obsidian 顶部主链接使用中国数字时代存档页 URL，避免微信原文失效后丢失可访问记录
- 如果能从 `CDT 档案卡` 读出原始来源链接，在正文前增加一行：`原始来源：[公众号名](微信原文链接)`

解析字段：
- 标题优先取 `<h1 class="entry-title">`，其次取 `og:title` / `<title>`
- 日期优先取页面标题下方的 `YYYY年M月D日`，其次取 `article:published_time` 或 JSON-LD `datePublished`
- 作者优先取 `CDT 档案卡` 中 `<strong>作者：</strong>` 后的链接文本
- 原始来源优先取 `CDT 档案卡` 中 `<strong>来源：</strong>` 后的链接文本和 `href`
- 正文只取 `<div class="post-content entry-content">` 内的主体段落

正文清理：
- 删除 `CDT 档案卡` 折叠块本身
- 删除 `版权说明`、`所在分类`、`标签`、相关文章、侧边栏、分享组件和页脚
- 正文从第一个真实文章段落开始，例如示例页从 `打开任何一个微信群、QQ群...` 开始
- 保留正文段落、引用和必要链接；不保留 CDT 导航、广告、专题、热门文章列表

推荐抓取与定位命令：
```bash
curl -L -x socks5://127.0.0.1:7897 -s "https://chinadigitaltimes.net/chinese/726746.html" \
  | sed -n '/<article id="post-/,/<div class="related-posts-content/p'
```

推荐识别原始微信来源：
```bash
curl -L -x socks5://127.0.0.1:7897 -s "https://chinadigitaltimes.net/chinese/726746.html" \
  | rg -n "CDT 档案卡|<strong>作者|<strong>来源|mp.weixin.qq.com|entry-title|article:published_time"
```

## 内容标签

根据 `/Users/zhangyaoxin/obsidian/文章/` 现有文章前 10 行提取，归档时优先从以下内容标签中选择 1-2 个，放在来源标签下方；`/Users/zhangyaoxin/obsidian/文章/tombkeeper/` 专题目录也沿用同一套内容标签规则。

- #中国政治
- #中国经济
- #社会民生
- #威权治理
- #言论审查
- #历史反思
- #意识形态
- #国际关系
- #公共财政
- #人口问题
- #医疗卫生
- #科技产业
- #教育公平
- #劳动就业
- #房地产
- #腐败特权
- #媒体传播
- #科技监控
- #法治人权
- #性别议题
- #文化生活

内容标签选择原则：
- 每篇文章默认 1-2 个内容标签，不堆叠多个弱相关标签
- 优先根据标题和正文主题判断，而不是根据来源判断
- 如果现有内容标签清单和文章主题明显不匹配，不要硬套弱相关标签；应提供最合适的新内容标签，并同步更新本 skill 的“内容标签”清单
- 新增内容标签必须是可复用的主题类别，不为单篇文章造过窄标签
- 内容标签和来源标签分离，例如 `#微信公众号` 是来源标签，不能替代内容标签
- 兼容旧文章打标签时，不修改文章标题、原始链接、来源标签和正文内容；如果文章没有来源标签，则把内容标签添加到原始链接下方；如果第一行就是来源标签，则添加到来源标签下方

## 使用流程

### 批量 URL 处理

当用户一次提供超过 3 篇文章 URL 时，必须使用 subagent 并发处理：
- 每篇文章分配给一个独立 subagent
- 每个 subagent 只处理自己的单个 URL，只写入对应的一篇 Markdown 文件
- subagent 必须先读取本 skill，再按本 skill 的文件格式、来源识别、内容标签和正文清理规则归档
- subagent 不得修改或回退其他文件，不得覆盖其他 subagent 创建的文件；如果目标文件已存在，先读取确认是否已经完整归档
- 如果当前 subagent 数量达到系统上限，先分配可用数量；已有 subagent 完成后关闭，再继续分配剩余 URL
- 主 agent 负责汇总每个 subagent 的结果，并在全部完成后统一验收

批量归档完成后的统一验收：
- 检查每个新文件是否存在
- 检查开头是否符合“链接行 → 来源标签 → 内容标签 → 正文/原始来源”格式
- 检查来源标签是否符合 URL 或 `CDT 档案卡` 的原始来源
- 检查内容标签是否为 1-2 个，且来自“内容标签”清单
- 检查正文中是否残留 `CDT 档案卡`、`版权说明`、`所在分类`、`标签`、`相关文章`、侧边栏、页脚或 HTML 标签
- 最终回复列出所有归档文件路径、来源标签、内容标签和验收结果

### 手动输入 URL
直接提供一个或多个 URL，我来抓取并归档。

### 抓取命令
```bash
# 使用代理抓取
curl -x socks5://127.0.0.1:7897 -s "URL" | sed -n '/<article/,/<\/article>/p' | sed 's/<[^>]*>//g'
```

### 解析要点
1. 提取标题（从 HTML `<title>` 或 `<h1>`）
2. 提取日期（从 meta 或 URL）
3. 提取正文（从 `<article>` 或 `<div class="content">`）
4. 清理 HTML 标签
5. 识别来源类型
6. 根据文章主题选择 1-2 个内容标签
7. 如果是中国数字时代存档页，先解析 `CDT 档案卡` 的原始来源；原始来源是微信时按微信公众号文章归档，并记录原始来源链接

## 示例

### 知乎文章

输入：手动 URL: `https://zhuanlan.zhihu.com/p/200925087`

输出文件：`/Users/zhangyaoxin/obsidian/文章/2007-02-01 谁谋杀了我们的游戏.md`

```markdown
[一篇远古文章：谁谋杀了我们的游戏？ - 知乎](https://zhuanlan.zhihu.com/p/200925087)

#知乎

#文化生活 #社会民生

失败！继续下一个失败！

就在此时，大量的游戏研发团队正在走向失败...
```

### 中国数字时代微信公众号存档页

输入：手动 URL: `https://chinadigitaltimes.net/chinese/726746.html`

输出文件：`/Users/zhangyaoxin/obsidian/文章/2026-04-24 世之介说｜当“不谈政治”成为群规，我们失去的是什么？.md`

```markdown
[世之介说｜当“不谈政治”成为群规，我们失去的是什么？](https://chinadigitaltimes.net/chinese/726746.html)

#微信公众号

#中国政治 #言论审查

原始来源：[世之介说](https://mp.weixin.qq.com/s/Fa1cRqV7dcYJmRJJJM_ISg)

打开任何一个微信群、QQ群，几乎都能在群公告里看到这样一条不成文的铁律：“不谈政治，违者移除。”

...
```
