#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_stats.py 的离线测试（不依赖真实内容库）。

运行：python -m unittest discover -s <skill目录>/scripts -p 'test_*.py' -v
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("practice_stats.py")
_spec = importlib.util.spec_from_file_location("practice_stats", SCRIPT)
stats = importlib.util.module_from_spec(_spec)
sys.modules["practice_stats"] = stats
_spec.loader.exec_module(stats)

PROGRESS = """# 刷题进度

## 一、第一阶段

### 数组

- [x] [1 两数之和](../algorithms/problems/01-two-sum.md) —— 哈希表
- [ ] [42 接雨水](../algorithms/problems/42-trapping-rain-water.md) —— 双指针

### 二叉树

- [x] [105 从前序与中序构造](../algorithms/problems/105-build-tree.md) —— 分治

## 三、错题本

| 题号 | 套路 | 卡点 | 状态 |
| --- | --- | --- | --- |
| LC 1 两数之和 | 哈希表 | 忘了存下标 | 2026-11-01 已 AC 3/3 |
"""

INDEX = """# 练习集

### 套路速查

| 套路           |  进度  |
| -------------- | :----: |
| [数组](#数组) | 2 / 2 |
| [二叉树](#二叉树) | 0 / 2 |

> 进度以 [刷题进度](../content/个人记录/刷题进度.md) 为准。✅ 标记跟随刷题记录（9 / 9）：105 从前序与中序构造、42 接雨水（2026-01-01 更新）。

### 数组

- ⬜ [1. 两数之和](P1TwoSum.java) · 🟢 · ★★★★★
- ⬜ [42. 接雨水](P42TrappingRainWater.java) · 🔴 · ★★★★★

### 二叉树

- ⬜ [105. 从前序与中序构造](P105.java) · 🟡 · ★★★★
- ⬜ 94. 二叉树的中序遍历 · 🟢 · ★★★
"""


class PracticeStatsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wiki = Path(self.tmp.name)
        (self.wiki / "content" / "个人记录").mkdir(parents=True)
        (self.wiki / "practice").mkdir()
        (self.wiki / stats.DEFAULT_PROGRESS).write_text(PROGRESS, encoding="utf-8")
        (self.wiki / stats.DEFAULT_INDEX).write_text(INDEX, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self):
        return stats.build_plan(self.wiki, stats.DEFAULT_PROGRESS, stats.DEFAULT_INDEX)

    def test_parse_progress_skips_mistakes_and_dedupes(self):
        items = stats.parse_progress(self.wiki / stats.DEFAULT_PROGRESS)
        self.assertEqual([(1, True), (42, False), (105, True)], [(n, c) for n, _, c in items])

    def test_plan_detects_drift(self):
        plan = self.plan()
        self.assertEqual([("数组", 1, 2), ("二叉树", 1, 2)], plan["stats"])
        self.assertEqual((2, 3), plan["summary_target"])
        joined = "；".join(plan["drift"])
        self.assertIn("数组", joined)
        self.assertIn("二叉树", joined)
        self.assertIn("✅ 标记与进度不一致：2 行", joined)
        self.assertEqual([], plan["info"]["未在索引出现的已做题目"])

    def test_fix_rewrites_counts_and_marks(self):
        plan = self.plan()
        stats.apply_fixes(plan, fix_list=False, dry_run=False)
        text = (self.wiki / stats.DEFAULT_INDEX).read_text(encoding="utf-8")
        self.assertIn("| [数组](#数组) | 1 / 2 |", text)
        self.assertIn("| [二叉树](#二叉树) | 1 / 2 |", text)
        self.assertIn("（2 / 3）", text)
        self.assertIn("- ✅ [1. 两数之和]", text)
        self.assertIn("- ⬜ [42. 接雨水]", text)
        self.assertEqual([], self.plan()["drift"])

    def test_fix_list_keeps_order_and_appends_missing(self):
        stats.apply_fixes(self.plan(), fix_list=True, dry_run=False)
        text = (self.wiki / stats.DEFAULT_INDEX).read_text(encoding="utf-8")
        self.assertIn("（2 / 3）：105 从前序与中序构造、1 两数之和", text)

    def test_dry_run_does_not_write(self):
        before = (self.wiki / stats.DEFAULT_INDEX).read_text(encoding="utf-8")
        stats.apply_fixes(self.plan(), fix_list=True, dry_run=True)
        self.assertEqual(before, (self.wiki / stats.DEFAULT_INDEX).read_text(encoding="utf-8"))

    def test_main_reports_clean_library(self):
        stats.apply_fixes(self.plan(), fix_list=False, dry_run=False)
        self.assertEqual(0, stats.main(["--wiki", str(self.wiki)]))


if __name__ == "__main__":
    unittest.main()
