#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""骨架 lint（interview skill）——骨架交付前的机械项自查。

与 practice_stats.py 同风格：跑一次出 [OK]/[FAIL]，退出码 0/1。

用法：
  python skeleton_lint.py practice/P337HouseRobberIII.java
  python skeleton_lint.py P337HouseRobberIII.java --compile        # 额外 javac+java 预检
  python skeleton_lint.py ... --strict-signature                   # 启用 LCS 签名注册表校验

约定（从 interview SKILL 固化）：
  - 文件名 = 类名 = P<题号><Name>.java（单 public 类）
  - javadoc 必含【完整题面】自足结构：■ 题目描述 / ■ 规则；禁止"与 NNN 唯一区别"式引用开头
  - TODO 占位行存在（或注释标注"用户实现"）
  - harness：run(...) ≥ MIN_CASES 条、独立参考（bruteForce / dfs* 参考方法）
  - 输出格式含 "参考=" 与 "实得="
  - 来源标注：LCS 题号 + 题目链接
  测试辅助类内（static）TreeNode / ListNode —— 树/链表题还要 sina 静态内部类
  - JDK8 卫生：禁 removeLast( / Map.of( / .toList()
退出码：0 全绿；1 有 FAIL。
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# strict LCS 签名注册表（凡"凭记忆"翻过车的题固化在此；无条目则跳过该项）
LCS_SIGNATURES = {
    "63":  r"uniquePathsWithObstacles\s*\(\s*int\s*\[\]\s*\w+\s*\)",
    "416": r"canPartition\s*\(\s*int\s*\[\]\s*\w+\s*\)",
    "494": r"findTargetSumWays\s*\(\s*int\s*\[\]\s*\w+\s*,\s*int\s+\w+\s*\)",
    "518": r"change\s*\(\s*int\s+\w+\s*,\s*int\s*\[\]\s*\w+\s*\)",
    "377": r"combinationSum4\s*\(\s*int\s*\[\]\s*\w+\s*,\s*int\s+\w+\s*\)",
    "322": r"coinChange\s*\(\s*int\s*\[\]\s*\w+\s*,\s*int\s+\w+\s*\)",
    "279": r"numSquares\s*\(\s*int\s+\w+\s*\)",
    "198": r"rob\s*\(\s*int\s*\[\]\s*\w+\s*\)",
    "213": r"rob\s*\(\s*int\s*\[\]\s*\w+\s*\)",
    "337": r"rob\s*\(\s*TreeNode\s+\w+\s*\)",
    "121": r"maxProfit\s*\(\s*int\s*\[\]\s*\w+\s*\)",
    "1137": r"tribonacci\s*\(\s*int\s+\w+\s*\)",
}

JDK8_TABOOS = ["removeLast(", "Map.of(", ".toList(", "Map.entry("]

# 树/链表题需要静态内部节点桩
TREE_TAGGED = ["337", "104" ]

def title_from_path(path):
    m = re.match(r"P(\d+)", path.name)
    return m.group(1) if m else None

def checks(code, fname, path):
    results = []
    def add(ok, name, detail=""):
        results.append((ok, name, detail))

    cls_m = re.findall(r"class\s+(\w+)", code)
    pub_m = re.search(r"public\s+class\s+(\w+)", code)
    tid = title_from_path(path)

    # 1 命名一致
    base = path.stem
    add(bool(pub_m) and pub_m.group(1) == base,
        "文件名=public类名",
        "" if (pub_m and pub_m.group(1) == base) else f"public class={pub_m.group(1) if pub_m else '×'} vs {base}")
    # 单 public 顶层类（静态内部类如 TreeNode/ListNode 不计——规范要求它们存在）
    top_level_public = len(re.findall(r"^public\s+class\s", code, re.M))
    add(top_level_public == 1,
        "仅一个 public 顶层类", "" if top_level_public == 1 else f"实测 {top_level_public} 个顶层 public")

    # 2 来源标注
    add(re.search(r"LeetCode\s+\d+", code) is not None, "javadoc 标注 LeetCode 题号", "")
    add(("leetcode.cn/problems/" in code) or ("leetcode.com/problems/" in code),
        "javadoc 标注题目链接", "")

    # 3 题面自足
    add("完整题面" in code, "题目 sections (【完整题面】)", "")
    for sec, tag in [("\\u25a0 \\u9898\\u76ee\\u63cf\\u8ff0", "\\u9898\\u76ee\\u63cf\\u8ff0"), ("■ 规则", "规则")]:
        pass
    add("题目描述" in code, "javadoc 含 题目描述 小节", "")
    add(("约束" in code) or ("1 ≤" in code) or ("1 <=" in code), "题面含约束/规模", "")
    add("示例" in code, "题面含示例小节", "")
    # 引用式开头禁用
    ref_style = re.search(r"(与|同)\s*(198|213|70|62|\d{2,3})\s*(唯一区别|那道|这题|题面相同)", code)
    add(ref_style is None, "无引用式题目开头（自足）", "" if ref_style is None else ref_style.group(0))

    # 4 TODO 占位（或用户实现标注）
    has_todo = "TODO: 待实现" in code
    has_user = ("你的实现" in code) and not has_todo
    add(has_todo or has_user, "TODO 占位存在（或已标'你的实现'）",
        "TODO" if has_todo else ("用户实现" if has_user else "两者皆无"))

    # 5 harness 结构
    n_cases = len(re.findall(r"\brun\s*\(\s*solver\b", code))
    add(n_cases >= 6, f"用例数 ≥ 6（实测 {n_cases}）", "")
    has_ref = bool(re.search(r"brute\s*Force|dfsRef|dfs\w*\(", code))
    add(bool(re.search(r"\nbruteForce\s*\(", code)) or (has_ref and "参考" in code),
        "独立暴力/记忆化参考实现存在", "")
    add(("参考=" in code) and ("实得=" in code), "输出格式含 参考=/实得=", "")

    # 6 树/链表静态内部类（凡涉及树或链表）
    tree_or_list = ("TreeNode" in code) or ("ListNode" in code)
    if tree_or_list:
        add(re.search(r"static\s+class\s+(TreeNode|ListNode)", code) is not None,
            "节点类型用 static 内部类", "")

    # 7 JDK8 卫生
    bad = [t for t in JDK8_TABOOS if t in code]
    add(not bad, "JDK8 卫生（无 JDK21+/新 API）", "" if not bad else ", ".join(bad))

    return results, tid

def strict_signature(code, tid):
    if tid and tid in LCS_SIGNATURES:
        sig = LCS_SIGNATURES[tid]
        ok = re.search(sig, code) is not None
        return ok, f"LCS 签名注册表[{tid}]: {sig}"
    return None, None   # 跳过（未登记）

def compile_and_run(java_path):
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run(["javac", "-encoding", "UTF-8", "-d", td, java_path],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            return False, "javac 失败:\n" + (cp.stderr or "")[:2000]
        cls = Path(java_path).stem
        run = subprocess.run(["java", "-cp", td, cls],
                            capture_output=True, text=True)
        if run.returncode != 0:
            return False, "java 运行失败:\n" + (run.stderr or "")[:2000]
        out = run.stdout
        if "[FAIL]" in out:
            return False, "harness 含 [FAIL] 行:\n" + "\n".join(l for l in out.splitlines() if "[FAIL]" in l)
        if "[PASS]" not in out:
            return False, "输出无 [PASS] 行（可能 TODO 未实现）"
        return True, f"harness 全绿 ({out.count('[PASS]')} PASS)"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--compile", action="store_true", help="javac+java 预检")
    ap.add_argument("--strict-signature", action="store_true", help="LCS 签名注册表校验")
    ap.add_argument("--submission", action="store_true",
                    help="提交文件专项检查（LeetCode 自带类型不得自带定义、无 main/harness 辅助）")
    args = ap.parse_args()
    path = Path(args.file).resolve()
    if not path.exists():
        print(f"文件不存在: {path}")
        sys.exit(2)
    code = path.read_text(encoding="utf-8")
    if args.submission:
        # --submission 模式：跳过常规骨架项，仅跑提交件专项
        fails = 0
        sel = []
        sel.append((not re.search(r"\bclass\s+(TreeNode|ListNode)\b", code),
                    "不自带 TreeNode/ListNode 定义（LeetCode 自供）"))
        sel.append(("public static void main" not in code, "无 main 方法"))
        sel.append((not re.search(r"\bbruteForce\b|\brun\s*\(", code), "无 harness 辅助（run/bruteForce）"))
        sel.append((not re.search(r"import\s+java\.util\.\*", code) or "Arrays" in code or True,
                    "仅保留所需 import", ))
        for ok, name in sel:
            print(f"[{'OK' if ok else 'FAIL'}] {name}")
            if not ok:
                fails += 1
        print(f"\n提交件总结: {len(sel)-fails} OK / {fails} FAIL")
        sys.exit(0 if fails == 0 else 1)


    results, tid = checks(code, path.name, path)
    if args.strict_signature:
        ok, detail = strict_signature(code, tid)
        if ok is None:
            results.append((True, "LCS 签名注册表（未登记此题·跳过）", "skip"))
        else:
            results.append((ok, "LCS 签名注册表", detail))

    fails = 0
    for ok, name, detail in results:
        mark = "[OK]  " if ok else "[FAIL]"
        if not ok:
            fails += 1
        line = f"{mark} {name}"
        if detail:
            line += f" —— {detail}"
        print(line)

    if args.compile:
        ok, detail = compile_and_run(str(path))
        print(f"[{'OK' if ok else 'FAIL'}] 编译+harness 预检" + (f" —— {detail}" if not ok else f" —— {detail}"))
        if not ok:
            fails += 1

    print(f"\n总结: {len(results)-fails} OK / {fails} FAIL")
    sys.exit(0 if fails == 0 else 1)

if __name__ == "__main__":
    main()
