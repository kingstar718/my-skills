#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""练习进度统计校准（interview-wiki 布局）。

真源：`progress_file` 里的勾选决定"哪些题做完"，`index_file` 各套路章节的题目行决定分母。
脚本据此校验并重写 `index_file` 的套路速查表、逐题 ✅ 标记与摘要（N / M）计数。

用法（在内容库根执行）：
  python practice_stats.py --check                    # 只报偏差，有漂移退出码 1
  python practice_stats.py --fix                      # 重写速查表、✅ 标记与（N / M）
  python practice_stats.py --fix --fix-list           # 同时重生成摘要里的题名清单
  python practice_stats.py --fix --dry-run            # 打印 diff 不落盘
  python practice_stats.py --wiki /path/to/interview-wiki

退出码：0 无需改动 / 已修正；1 --check 发现漂移；2 环境或解析错误。
"""

import argparse
import datetime
import difflib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_PROGRESS = "content/个人记录/刷题进度.md"
DEFAULT_INDEX = "practice/README.md"

RE_CHECK = re.compile(r"^- \[( |x|X)\] (.*)$")
RE_PROGRESS_NUM = re.compile(r"^\[(\d+)[\s.、]([^\]]+)\]")
RE_PROGRESS_PLAIN = re.compile(r"^(\d+)[\s.、](.+)$")
RE_SECTION = re.compile(r"^### (.+?)\s*$")
RE_TABLE_ROW = re.compile(r"^\|\s*\[([^\]]+)\]\(#[^)]+\)\s*\|\s*(\d+)\s*/\s*(\d+)\s*\|\s*$")
RE_ITEM_ROW = re.compile(r"^- (✅|⬜) (.*)$")
RE_SUMMARY_COUNT = re.compile(r"(✅ 标记跟随刷题记录（)(\d+)( / )(\d+)(）)")
RE_SUMMARY_LIST = re.compile(r"(✅ 标记跟随刷题记录（\d+ / \d+）：)(.*?)(（\d{4}-\d{2}-\d{2} 更新）)")
RE_DATE = re.compile(r"（\d{4}-\d{2}-\d{2} 更新）")


def locate_wiki(explicit):
    """定位内容库根：显式参数 → 当前目录 → 环境变量。"""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.cwd())
    env = os.environ.get("INTERVIEW_WIKI")
    if env:
        candidates.append(Path(env))
    for path in candidates:
        if (path / "content").is_dir() and (path / "practice").is_dir():
            return path.resolve()
    raise SystemExit(
        "未找到内容库：需含 content/ 与 practice/。用 --wiki <dir> 或 INTERVIEW_WIKI 指定。"
    )


def parse_progress(path):
    """解析进度文件：返回 [(题号, 题名, 是否勾选)]，按文档顺序去重。"""
    items, seen = [], set()
    in_mistakes = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_mistakes = "错题本" in line
            continue
        if in_mistakes:
            continue
        m = RE_CHECK.match(line)
        if not m:
            continue
        checked, rest = m.group(1).lower() == "x", m.group(2).strip()
        parsed = RE_PROGRESS_NUM.match(rest) or RE_PROGRESS_PLAIN.match(rest)
        if not parsed:
            continue
        num = int(parsed.group(1))
        if num in seen:
            continue
        seen.add(num)
        items.append((num, parsed.group(2).strip(), checked))
    return items


def parse_index(path):
    """解析索引：返回 (速查表 [(套路, done, total)], {套路: [(行号, 题号, 已标✅)]})。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    table, sections = [], {}
    current = None
    for i, line in enumerate(lines):
        m = RE_SECTION.match(line)
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        row = RE_TABLE_ROW.match(line)
        if row:
            table.append((row.group(1), int(row.group(2)), int(row.group(3))))
            continue
        item = RE_ITEM_ROW.match(line)
        if item and current:
            num = item_number(item.group(2))
            if num is not None:
                sections[current].append((i, num, item.group(1) == "✅"))
    return table, sections


def item_number(rest):
    """从题目行剩余部分取题号。"""
    head = rest.split(" · ")[0].strip()
    m = re.match(r"^\[(\d+)[\s.、]", head) or re.match(r"^(\d+)[\s.、]", head)
    return int(m.group(1)) if m else None


def build_plan(wiki, progress_rel, index_rel):
    progress_path = wiki / progress_rel
    index_path = wiki / index_rel
    for p in (progress_path, index_path):
        if not p.is_file():
            raise SystemExit(f"缺少文件：{p}")

    items = parse_progress(progress_path)
    done = {num for num, _, checked in items if checked}
    names = {num: name for num, name, _ in items}
    table, sections = parse_index(index_path)

    stats, drift, fixes = [], [], []
    for name, recorded_done, recorded_total in table:
        rows = sections.get(name)
        if rows is None:
            drift.append(f"速查表套路「{name}」在正文找不到同名章节")
            continue
        total = len(rows)
        actual_done = sum(1 for _, num, _ in rows if num in done)
        stats.append((name, actual_done, total))
        if (recorded_done, recorded_total) != (actual_done, total):
            drift.append(
                f"速查表「{name}」写 {recorded_done}/{recorded_total}，应为 {actual_done}/{total}"
            )
            fixes.append(("table", name, actual_done, total))

    wrong_marks = 0
    for name, rows in sections.items():
        for line_no, num, marked in rows:
            expected = num in done
            if marked is expected:
                continue
            wrong_marks += 1
            fixes.append(("item", line_no, "✅" if expected else "⬜"))
    if wrong_marks:
        drift.append(f"逐题 ✅ 标记与进度不一致：{wrong_marks} 行")

    summary = RE_SUMMARY_COUNT.search(index_path.read_text(encoding="utf-8"))
    actual_total_done = len(done)
    actual_total = len(items)
    if summary:
        recorded = (int(summary.group(2)), int(summary.group(4)))
        if recorded != (actual_total_done, actual_total):
            drift.append(
                f"摘要写 {recorded[0]} / {recorded[1]}，应为 {actual_total_done} / {actual_total}"
            )
            fixes.append(("summary", actual_total_done, actual_total))

    listed = {num for rows in sections.values() for _, num, _ in rows}
    info = {
        "未在索引出现的已做题目": sorted(n for n in done if n not in listed),
        "索引有但进度未登记": sorted(listed - {num for num, _, _ in items}),
    }
    order = [num for num, _, _ in items if num in done]
    return {
        "wiki": str(wiki),
        "stats": stats,
        "drift": drift,
        "fixes": fixes,
        "info": info,
        "summary_target": (actual_total_done, actual_total),
        "done_order": order,
        "names": {str(k): v for k, v in names.items()},
        "paths": (progress_path, index_path),
    }


def apply_fixes(plan, fix_list, dry_run):
    _, index_path = plan["paths"]
    lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    for fix in plan["fixes"]:
        if fix[0] == "table":
            _, name, actual_done, total = fix
            for i, line in enumerate(lines):
                row = RE_TABLE_ROW.match(line.rstrip("\n"))
                if row and row.group(1) == name:
                    lines[i] = re.sub(
                        r"(\|\s*\d+\s*/\s*)\d+(\s*\|\s*)$",
                        rf"\g<1>{total}\g<2>",
                        line,
                    )
                    lines[i] = re.sub(
                        r"(\|\s*)\d+(\s*/\s*\d+\s*\|\s*)$",
                        rf"\g<1>{actual_done}\g<2>",
                        lines[i],
                    )
                    break
        elif fix[0] == "item":
            _, line_no, mark = fix
            lines[line_no] = re.sub(r"^- (✅|⬜)", f"- {mark}", lines[line_no], count=1)
        elif fix[0] == "summary":
            _, done_n, total_n = fix
            joined = "".join(lines)
            joined = RE_SUMMARY_COUNT.sub(rf"\g<1>{done_n}\g<3>{total_n}\g<5>", joined)
            lines = joined.splitlines(keepends=True)

    if fix_list:
        joined = "".join(lines)
        found = RE_SUMMARY_LIST.search(joined)
        if found:
            old_list = found.group(2)
            names, done_order = plan["names"], plan["done_order"]
            done_set = set(done_order)
            kept = [
                int(n)
                for n in (m.group(1) for m in re.finditer(r"(?:^|、)(\d+)\s", old_list))
                if int(n) in done_set
            ]
            ordered = kept + [n for n in done_order if n not in kept]
            new_list = "、".join(f"{n} {names.get(str(n), '')}".strip() for n in ordered)
            if new_list != old_list:
                joined = (
                    joined[: found.start(2)]
                    + new_list
                    + joined[found.end(2):]
                )
                new_date = f"（{datetime.date.today().isoformat()} 更新）"
                joined = RE_DATE.sub(new_date, joined, count=1)
            lines = joined.splitlines(keepends=True)

    new_text = "".join(lines)
    old_text = index_path.read_text(encoding="utf-8")
    if new_text == old_text:
        print("无需改动。")
        return 0
    if dry_run:
        sys.stdout.writelines(
            difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=str(index_path),
                tofile=str(index_path) + " (修正后)",
            )
        )
        return 0
    index_path.write_text(new_text, encoding="utf-8")
    print(f"已更新：{index_path}")
    return 0


def report(plan):
    print("套路进度（完成 / 总数）")
    for name, done_n, total_n in plan["stats"]:
        print(f"  {name:<14} {done_n:>3} / {total_n:<3}")
    done_n, total_n = plan["summary_target"]
    print(f"\n汇总：{done_n} / {total_n}（进度口径）")
    missing = plan["info"]["未在索引出现的已做题目"]
    if missing:
        print(
            f"缺索引行的已做题目（{len(missing)} 道）：{missing}\n"
            f"  这些题已完成但未出现在任何套路章节，补行后重跑才能让速查表反映真实进度。"
        )
    if plan["drift"]:
        print("\n漂移：")
        for line in plan["drift"]:
            print(f"  - {line}")
    else:
        print("\n无漂移。")


def main(argv=None):
    parser = argparse.ArgumentParser(description="练习进度统计校准")
    parser.add_argument("--wiki", help="内容库根目录（含 content/ 与 practice/）")
    parser.add_argument("--progress", default=DEFAULT_PROGRESS, help="进度文件（相对内容库根）")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="索引文件（相对内容库根）")
    parser.add_argument("--check", action="store_true", help="只校验（默认行为），有漂移退出码 1")
    parser.add_argument("--fix", action="store_true", help="重写速查表、✅ 标记与计数")
    parser.add_argument("--fix-list", action="store_true", help="同时重生成摘要题名清单")
    parser.add_argument("--dry-run", action="store_true", help="配合 --fix，只打印 diff")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    plan = build_plan(locate_wiki(args.wiki), args.progress, args.index)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
    else:
        report(plan)

    if not args.fix:
        return 1 if plan["drift"] else 0
    apply_fixes(plan, args.fix_list, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
