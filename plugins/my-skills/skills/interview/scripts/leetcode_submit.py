#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LeetCode 提交脚本（非官方接口，基于会话 Cookie，默认 leetcode.cn）。

用法：
  python leetcode_submit.py --slug remove-element --file Solution.java
  python leetcode_submit.py --slug two-sum --file Solution.java --site global

退出码：
  0  Accepted
  1  判题完成但未通过（WA/TLE/MLE/RE/CE 等）
  2  配置/网络/未知错误

Cookie 配置文件默认 ~/.my-interview/leetcode_cookies.json：
  {"LEETCODE_SESSION": "...", "csrftoken": "..."}
也可用环境变量 LEETCODE_SESSION / LEETCODE_CSRFTOKEN 覆盖。
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".my-interview", "leetcode_cookies.json")
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SITES = {
    "cn": {
        "origin": "https://leetcode.cn",
        "graphql": "https://leetcode.cn/graphql/",
        "submit": "https://leetcode.cn/problems/{slug}/submit/",
        "check": "https://leetcode.cn/submissions/detail/{sid}/check/",
    },
    "global": {
        "origin": "https://leetcode.com",
        "graphql": "https://leetcode.com/graphql",
        "submit": "https://leetcode.com/problems/{slug}/submit/",
        "check": "https://leetcode.com/submissions/detail/{sid}/check/",
    },
}


class SubmitError(Exception):
    pass


def parse_cookie_string(cookie_str):
    """从浏览器复制的整段 Cookie 中提取键值（按第一个 = 分割）。"""
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition("=")
        key = key.strip()
        if key:
            result[key] = value.strip()
    return result

def prompt_cookies():
    """交互式粘贴 Cookie（不回显，值不经过命令行/文件）。非交互终端返回空。"""
    if not sys.stdin.isatty():
        return {}
    import getpass
    print("请粘贴 LeetCode Cookie（不会回显）：")
    session = getpass.getpass("LEETCODE_SESSION: ").strip()
    csrf = getpass.getpass("csrftoken: ").strip()
    return {"LEETCODE_SESSION": session, "csrftoken": csrf}


def load_cookies(path, cookie_arg=None, session_arg=None, csrf_arg=None):
    """优先级：--cookie 整段 > --session/--csrf 参数 > 环境变量 > 配置文件 > 交互式粘贴。"""
    cookies = {}
    if cookie_arg:
        parsed = parse_cookie_string(cookie_arg)
        cookies.update({k: v for k, v in parsed.items() if k in ("LEETCODE_SESSION", "csrftoken") and v})
    if session_arg:
        cookies["LEETCODE_SESSION"] = session_arg
    if csrf_arg:
        cookies["csrftoken"] = csrf_arg
    env_session = os.environ.get("LEETCODE_SESSION")
    env_csrf = os.environ.get("LEETCODE_CSRFTOKEN")
    if not cookies.get("LEETCODE_SESSION") and env_session:
        cookies["LEETCODE_SESSION"] = env_session
    if not cookies.get("csrftoken") and env_csrf:
        cookies["csrftoken"] = env_csrf
    if (not cookies.get("LEETCODE_SESSION") or not cookies.get("csrftoken")) and path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            file_cookies = json.load(f)
        if not cookies.get("LEETCODE_SESSION") and file_cookies.get("LEETCODE_SESSION"):
            cookies["LEETCODE_SESSION"] = file_cookies["LEETCODE_SESSION"]
        if not cookies.get("csrftoken") and file_cookies.get("csrftoken"):
            cookies["csrftoken"] = file_cookies["csrftoken"]
    if not cookies.get("LEETCODE_SESSION") or not cookies.get("csrftoken"):
        cookies.update(prompt_cookies())
    missing = [k for k in ("LEETCODE_SESSION", "csrftoken") if not cookies.get(k)]
    if missing:
        raise SubmitError(
            "缺少 Cookie: %s。任选一种给法：--session/--csrf 参数、LEETCODE_SESSION/LEETCODE_CSRFTOKEN 环境变量、"
            "配置文件 %s；或在交互终端直接运行脚本粘贴。" % ("、".join(missing), DEFAULT_COOKIE_FILE)
        )
    return cookies


def request(url, payload=None, headers=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise SubmitError("HTTP %d 返回非 JSON（可能 Cookie 失效或触发风控）：%s" % (e.code, body[:200]))
    except urllib.error.URLError as e:
        raise SubmitError("网络错误：%s" % e.reason)


def base_headers(site, cookies, slug=None):
    referer = site["origin"] + ("/problems/%s/" % slug if slug else "/")
    return {
        "User-Agent": DEFAULT_UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": site["origin"],
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "LEETCODE_SESSION=%s; csrftoken=%s" % (cookies["LEETCODE_SESSION"], cookies["csrftoken"]),
        "x-csrftoken": cookies["csrftoken"],
    }


def fetch_question_id(site, slug, cookies):
    payload = {
        "query": "query questionData($titleSlug: String!) { question(titleSlug: $titleSlug) { questionId title titleSlug } }",
        "variables": {"titleSlug": slug},
        "operationName": "questionData",
    }
    data = request(site["graphql"], payload, base_headers(site, cookies))
    question = (data.get("data") or {}).get("question")
    if not question:
        raise SubmitError(
            "未找到题目 slug=%s（检查拼写，如 27-remove-element.md 对应 remove-element）" % slug)
    return int(question["questionId"]), question.get("title", slug)


def submit_code(site, slug, question_id, lang, code, cookies):
    payload = {
        "lang": lang,
        "question_id": question_id,
        "typed_code": code,
        "test_mode": False,
        "judge_type": "large",
    }
    data = request(site["submit"].format(slug=slug), payload, base_headers(site, cookies, slug))
    sid = data.get("submission_id")
    if not sid:
        raise SubmitError("提交失败：%s" % json.dumps(data, ensure_ascii=False)[:300])
    return sid


def poll_result(site, sid, cookies, timeout, interval):
    deadline = time.time() + timeout
    while True:
        data = request(site["check"].format(sid=sid), None, base_headers(site, cookies))
        if data.get("state") == "SUCCESS":
            return data
        if time.time() >= deadline:
            raise SubmitError("判题超时（%ds），可稍后手动查看 https://leetcode.cn/submissions/detail/%s/" % (timeout, sid))
        time.sleep(interval)


def truncate(text, limit=1500):
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "...(截断)"


def print_result(result):
    status_code = result.get("status_code")
    status_msg = result.get("status_msg") or ("状态码 %s" % status_code)
    line = "[%s] %s" % ("AC" if status_code == 10 else "!!", status_msg)
    if result.get("runtime"):
        line += " | runtime=%sms" % result["runtime"]
    if result.get("memory"):
        line += " | memory=%s" % result["memory"]
    if result.get("total_testcases") is not None:
        line += " | passed=%s/%s" % (result.get("total_correct"), result["total_testcases"])
    print(line)

    if status_code == 10:
        return 0

    if result.get("last_testcase"):
        print("-- last_testcase --")
        print(truncate(result["last_testcase"]))
    if result.get("expected_output"):
        print("-- expected --")
        print(truncate(result["expected_output"]))
    if result.get("code_output"):
        print("-- actual --")
        print(truncate(result["code_output"]))
    if result.get("compile_error"):
        print("-- compile error --")
        print(truncate(result["compile_error"]))
    return 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="LeetCode 提交脚本（Cookie 认证，默认 leetcode.cn）")
    parser.add_argument("--slug", required=True, help="题目 titleSlug，如 remove-element")
    parser.add_argument("--file", required=True, help="待提交的 Java 文件（必须是 class Solution 形式）")
    parser.add_argument("--site", choices=sorted(SITES), default="cn", help="cn=leetcode.cn(默认)，global=leetcode.com")
    parser.add_argument("--lang", default="java", help="提交语言，默认 java")
    parser.add_argument("--cookies", default=DEFAULT_COOKIE_FILE, help="Cookie 配置文件路径")
    parser.add_argument("--session", help="LEETCODE_SESSION cookie（临时传值，用完即弃）")
    parser.add_argument("--cookie", help="完整的 Cookie 头字符串（浏览器复制的整段），自动提取 LEETCODE_SESSION 与 csrftoken")
    parser.add_argument("--csrf", help="csrftoken cookie（临时传值，用完即弃）")
    parser.add_argument("--timeout", type=int, default=60, help="判题轮询超时秒数，默认 60")
    parser.add_argument("--poll-interval", type=int, default=2, help="轮询间隔秒数，默认 2")
    args = parser.parse_args()

    try:
        cookies = load_cookies(args.cookies, args.cookie, args.session, args.csrf)
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
        site = SITES[args.site]
        question_id, title = fetch_question_id(site, args.slug, cookies)
        print("提交 %s (%s)..." % (title, args.slug))
        sid = submit_code(site, args.slug, question_id, args.lang, code, cookies)
        print("submission_id=%s，等待判题..." % sid)
        result = poll_result(site, sid, cookies, args.timeout, args.poll_interval)
        return print_result(result)
    except SubmitError as e:
        print("[ERROR] %s" % e, file=sys.stderr)
        return 2
    except OSError as e:
        print("[ERROR] 文件/网络异常：%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())