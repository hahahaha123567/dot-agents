---
name: cursor-usage-csv
description: Aggregates locally saved Cursor usage CSV by model with Chinese 万/亿 formatting and total-descending sort; default workflow scans ~/Downloads for .csv files modified within 10 minutes (newest mtime) so the user need not paste full paths. Does not fetch URLs—only local files. Use when the user exports Cursor usage to disk, mentions Downloads, or wants per-model token breakdown without typing file paths.
---

# Cursor usage.csv 用量汇总

## 何时使用

用户已在 **本机** 保存 **Cursor 导出的用量 CSV**，需要按 **Model** 汇总各列 token。**不要**尝试用脚本从网页或 API 下载 CSV，只处理本地文件。

| 含义 | CSV 列名 |
| --- | --- |
| 带 cache 写入的输入 | `Input (w/ Cache Write)` |
| 不带 cache 写入的输入 | `Input (w/o Cache Write)` |
| 缓存读取 | `Cache Read` |
| 输出 | `Output Tokens` |
| 合计（参考） | `Total Tokens` |

## 默认操作（不要求用户提供完整路径）

用户将导出保存到本机 **下载目录** 后，代理**不要**要求用户粘贴完整路径，除非自动查找失败。

1. 请用户确认已在 Cursor / 浏览器中 **导出** 并将 CSV **保存**到下载目录（默认 **`~/Downloads`**，本机即 **`/Users/zhangyaoxin/Downloads`**）。
2. 在终端执行（**无参数**即可触发扫描）：

```bash
python3 ~/.cursor/skills/cursor-usage-csv/scripts/aggregate_usage.py
```

3. 脚本行为：
   - 扫描 **`~/Downloads`**（可用环境变量 `CURSOR_USAGE_DOWNLOADS_DIR` 覆盖为绝对路径）下所有 **`.csv`**；
   - 只保留 **修改时间距当前不超过 10 分钟** 的文件（窗口可用 `CURSOR_USAGE_MAX_AGE_SEC` 覆盖，默认 `600` 秒）；
   - 若有多份命中，取 **mtime 最新** 的一个；
   - 首行输出 `# 使用文件: …`，便于核对。
4. 将脚本 **完整终端输出**（含 `# 使用文件` 与表格）原样提供给用户。

等价的显式自动模式：`--auto` 或 `-a`。

## 显式本地路径（可选）

用户已给出 **绝对路径** 时，作为唯一参数传入：

```bash
python3 ~/.cursor/skills/cursor-usage-csv/scripts/aggregate_usage.py "/path/to/usage-events.csv"
```

## 输出格式

- 数字为 **中文习惯**：≥1 万为「X.XX万」，≥1 亿为「X.XX亿」，无英文 k/m/b 或千分位逗号。
- 各行按 **`Total Tokens` 降序**（同 Total 时按 Model 名升序）。

## 列名与假设

- 表头需包含：`Model`、`Input (w/ Cache Write)`、`Input (w/o Cache Write)`、`Cache Read`、`Output Tokens`、`Total Tokens`。
- 若某行某列为空或非数字，按 **0** 处理。

## 脚本位置

- [scripts/aggregate_usage.py](scripts/aggregate_usage.py)

## 故障排查

- **未找到最近 10 分钟内的 .csv**：请用户确认已保存导出到 `~/Downloads`，或设置 `CURSOR_USAGE_MAX_AGE_SEC` 放宽窗口，或传入**本地**文件路径。
- **用户只贴了 https 链接**：说明需先自行下载/保存到本机后再跑脚本；脚本**不会**请求 URL。
- **列名不匹配**：若 Cursor 改表头，需同步更新脚本中的 `row.get("...")` 键名。
