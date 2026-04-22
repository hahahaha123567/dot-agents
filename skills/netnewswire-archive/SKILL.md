---
name: netnewswire-archive
description: 从 NetNewsWire starred 文章或手动 URL 抓取完整原文，归档到 Obsidian
---

## 功能

1. 从 NetNewsWire 获取 starred 文章列表
2. 或接受手动输入的 URL
3. 抓取完整原文（使用 curl + 代理）
4. 解析文章内容
5. 归档到 Obsidian

## 网络代理

端口：`socks5://127.0.0.1:7897`

## 目标文件格式

**文件位置：** `/Users/zhangyaoxin/obsidian/文章/`

**文件名：** `YYYY-MM-DD 文章标题.md`

**文件内容格式：**
```markdown
[文章标题](原文链接)

#宏观标签1 #宏观标签2

#来源类型

文章正文
```

## 来源类型识别

根据 URL 或抓取内容判断：
- `weibo.com` → #微博
- `m.weibo.cn` → #微博
- `mp.weixin.qq.com` → #微信公众号
- `nytimes.com` → #纽约时报
- `wsj.com` → #华尔街日报
- `ft.com` → #金融时报
- `bbc.com` → #BBC
- `cnn.com` → #CNN
- `theguardian.com` → #卫报
- `zhihu.com` → #知乎
- 包含 "微信公众号" → #微信公众号
- 其他 → #博客

## 特殊 URL 处理

### 微博 URL 转换
- 输入：`https://weibo.com/1401527553/Qd0InF4EQ`
- 提取末尾 ID：`Qd0InF4EQ`
- 转换为：`https://m.weibo.cn/detail/Qd0InF4EQ`
- 原因：m.weibo.cn 是移动版，通常不需要登录验证

## 宏观标签

根据文章主题选择 1-2 个：
- #游戏
- #娱乐
- #科技
- #经济
- #政治
- #社会
- #历史
- #文化
- #教育
- #健康
- #其他

## 使用流程

### 方式一：从 NetNewsWire starred 获取
```bash
# 1. 获取 starred 文章列表
sqlite3 ~/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application\ Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3 \
  "SELECT articleID, title, url, datePublished FROM articles a JOIN statuses s ON a.articleID = s.articleID WHERE s.starred = 1 ORDER BY datePublished DESC"

# 2. 获取单篇文章详情
sqlite3 ~/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application\ Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3 \
  "SELECT title, url, contentHTML, datePublished FROM articles WHERE articleID = 'xxx'"
```

### 方式二：手动输入 URL
直接提供 URL，我来抓取

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

## 示例

输入：从 NetNewsWire 获取 URL: `https://zhuanlan.zhihu.com/p/200925087`

输出文件：`/Users/zhangyaoxin/obsidian/文章/2007-02-01 谁谋杀了我们的游戏.md`

```markdown
[一篇远古文章：谁谋杀了我们的游戏？ - 知乎](https://zhuanlan.zhihu.com/p/200925087)

#游戏 #娱乐

#文章来源 #知乎

失败！继续下一个失败！

就在此时，大量的游戏研发团队正在走向失败...
```
