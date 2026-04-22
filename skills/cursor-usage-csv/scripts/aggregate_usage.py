#!/usr/bin/env python3
"""Aggregate Cursor usage.csv by model (local files only)."""

import csv
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# 默认：~/Downloads 内「最近修改」时间在窗口内的 .csv；多文件取 mtime 最新
DEFAULT_MAX_AGE_SEC = 600


def to_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def downloads_dir() -> Path:
    raw = os.environ.get("CURSOR_USAGE_DOWNLOADS_DIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / "Downloads").resolve()


def max_age_sec() -> int:
    try:
        return int(os.environ.get("CURSOR_USAGE_MAX_AGE_SEC", str(DEFAULT_MAX_AGE_SEC)))
    except ValueError:
        return DEFAULT_MAX_AGE_SEC


def find_recent_downloads_csv() -> Path | None:
    """在下载目录中找更新时间距现在不超过 max_age 的 .csv；多个则取 mtime 最新。"""
    root = downloads_dir()
    if not root.is_dir():
        return None
    now = time.time()
    window = max_age_sec()
    best: tuple[float, Path] | None = None
    for p in root.iterdir():
        if not p.is_file() or p.suffix.lower() != ".csv":
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        age = now - mtime
        if age < 0:
            age = 0
        if age > window:
            continue
        if best is None or mtime > best[0]:
            best = (mtime, p)
    return best[1] if best else None


def load_rows(local_path):
    p = str(local_path).strip()
    if p.startswith(("http://", "https://")):
        print(
            "不支持通过 URL 拉取 CSV，请先在浏览器导出并保存到本机，再使用无参数扫描或传入本地路径。",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def format_cn_wan_yi(n: int) -> str:
    """中文习惯：≥1 亿用「亿」，≥1 万用「万」，否则阿拉伯数字；去掉多余小数末尾 0。"""
    if n == 0:
        return "0"
    if n >= 100_000_000:
        v = n / 100_000_000
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return f"{s}亿"
    if n >= 10_000:
        v = n / 10_000
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return f"{s}万"
    return str(n)


def aggregate(rows):
    usage = defaultdict(
        lambda: {
            "input_cache_write": 0,
            "input_no_cache": 0,
            "cache_read": 0,
            "output": 0,
            "total": 0,
        }
    )
    for row in rows:
        model = row.get("Model") or ""
        usage[model]["input_cache_write"] += to_int(row.get("Input (w/ Cache Write)", ""))
        usage[model]["input_no_cache"] += to_int(row.get("Input (w/o Cache Write)", ""))
        usage[model]["cache_read"] += to_int(row.get("Cache Read", ""))
        usage[model]["output"] += to_int(row.get("Output Tokens", ""))
        usage[model]["total"] += to_int(row.get("Total Tokens", ""))
    return usage


def print_report(usage):
    # 按 Total Tokens 从大到小；Total 相同则按 Model 名稳定排序
    ordered = sorted(usage.items(), key=lambda kv: (-kv[1]["total"], kv[0]))
    w = 14  # 万/亿 字符串宽度（等宽字体下大致对齐）
    print(
        f"{'Model':<28} {'Input(Cache)':>{w}} {'Input(NoCache)':>{w}} "
        f"{'Cache Read':>{w}} {'Output':>{w}} {'Total':>{w}}"
    )
    print("-" * (28 + 5 * (w + 1)))
    for model, data in ordered:
        print(
            f"{model:<28} "
            f"{format_cn_wan_yi(data['input_cache_write']):>{w}} "
            f"{format_cn_wan_yi(data['input_no_cache']):>{w}} "
            f"{format_cn_wan_yi(data['cache_read']):>{w}} "
            f"{format_cn_wan_yi(data['output']):>{w}} "
            f"{format_cn_wan_yi(data['total']):>{w}}"
        )


def main():
    args = [a.strip() for a in sys.argv[1:] if a.strip()]
    if not args or args[0] in ("--auto", "-a"):
        csv_path = find_recent_downloads_csv()
        if csv_path is None:
            d = downloads_dir()
            w = max_age_sec()
            print(
                f"未在 {d} 中找到最近 {w // 60} 分钟内更新过的 .csv。"
                "请先将 Cursor 导出的 CSV 保存到该目录，或设置 CURSOR_USAGE_DOWNLOADS_DIR / CURSOR_USAGE_MAX_AGE_SEC，"
                "或直接传入本地文件路径。",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"# 使用文件: {csv_path}")
    elif len(args) == 1:
        csv_path = args[0]
    else:
        print(
            "Usage: aggregate_usage.py [--auto|-a] [<usage.csv 本地路径>]",
            "  无参数或 --auto：扫描下载目录（默认 ~/Downloads，见 CURSOR_USAGE_DOWNLOADS_DIR）中",
            f"  最近 {max_age_sec() // 60} 分钟内修改的 .csv，多文件取 mtime 最新。",
            "  环境变量: CURSOR_USAGE_DOWNLOADS_DIR, CURSOR_USAGE_MAX_AGE_SEC（秒）",
            sep="\n",
            file=sys.stderr,
        )
        sys.exit(1)
    rows = load_rows(csv_path)
    usage = aggregate(rows)
    print_report(usage)


if __name__ == "__main__":
    main()
