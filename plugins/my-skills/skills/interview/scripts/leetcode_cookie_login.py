#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
leetcode_cookie_login.py —— 浏览器扫码/登录，自动抓取 leetcode.cn 的 LEETCODE_SESSION 与 csrftoken

用法（在自己能看见浏览器的机器上跑）：
    python3 leetcode_cookie_login.py            # 弹窗扫码或登录，登录成功后自动保存并退出
    python3 leetcode_cookie_login.py --account 936016045@qq.com   # 账号密码登录（密码交互输入，不回显）
    python3 leetcode_cookie_login.py --phone 13800138000          # 手机号+短信验证码登录（验证码交互输入）
    python3 leetcode_cookie_login.py --account <账号> --password <密码>  # 密码直接传（不推荐，会进 shell 历史）
    python3 leetcode_cookie_login.py --phone <手机号> --code <验证码>   # 验证码直接传（不推荐）
    python3 leetcode_cookie_login.py --timeout 120   # 登录等待上限（默认 600 秒）
    python3 leetcode_cookie_login.py --headless      # 无头调试用（正常登录请勿用）

依赖：pip install playwright && python3 -m playwright install chromium

保存位置：~/.my-interview/leetcode_cookies.json（权限 600，不入 git）
提交脚本 leetcode_submit.py 会自动读取该文件，之后提交无需再传 cookie。

安全说明：cookie 是账号凭证。脚本只在内存与上述 JSON 中出现，不打印完整值、
不写日志；文件权限 600；过期后重跑本脚本即可。
"""

import argparse
import json
import os
import sys
import time

COOKIE_FILE = os.path.expanduser("~/.my-interview/leetcode_cookies.json")
LOGIN_URL = "https://leetcode.cn/accounts/login/"
POLL_INTERVAL = 2

# 弱化自动化检测：正常 UA + 去掉 AutomationControlled 标记
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="扫码/登录 leetcode.cn 并保存 cookie")
    parser.add_argument("--timeout", type=int, default=600,
                        help="等待登录完成的最长秒数（默认 600）")
    parser.add_argument("--headless", action="store_true",
                        help="无头模式（仅调试用，正常登录会弹浏览器窗口）")
    login = parser.add_mutually_exclusive_group()
    login.add_argument("--account", default=None,
                       help="账号（邮箱/手机号/用户名）——密码登录：切密码页签→自动填账号+密码→提交")
    login.add_argument("--phone", default=None,
                       help="手机号——短信验证码登录：切页签→勾协议→填手机号→点获取验证码→输码→登录")
    parser.add_argument("--password", default=None,
                        help="账号密码登录的密码。不传则交互输入（不回显，推荐）；也可用环境变量 LEETCODE_PASSWORD")
    parser.add_argument("--code", default=None,
                        help="短信验证码。不传则交互输入")
    parser.add_argument("--shot", default=None,
                        help="页面加载后截图保存路径（如扫码前取证），例：--shot /tmp/lc_qr.png")
    parser.add_argument("--qr-expand", action="store_true",
                        help="截图前等待 4s 并点击二维码容器右上角（展开/刷新二维码），扫码用")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="zh-CN",
            viewport={"width": 1280, "height": 800},
        )
        if not args.headless:
            context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        page = context.new_page()
        try:
            print("正在打开 leetcode.cn 登录页 …（浏览器窗口里扫二维码登录即可）")
            page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
            if args.shot:
                page.wait_for_timeout(4000)
                if args.qr_expand:
                    clicked_something = False
                    # 1) 切到扫码面板：先点 #qr-code-login（实测有效）
                    try:
                        qr_btn = page.locator("#qr-code-login")
                        if qr_btn.count() > 0 and qr_btn.is_visible():
                            qr_btn.click()
                            print("已点击 #qr-code-login 切换到扫码面板")
                            clicked_something = True
                    except Exception as e:
                        print(f"#qr-code-login 点击失败（{type(e).__name__}）")
                    # 2) 兜底：文本搜索其他展开/刷新控件
                    if not clicked_something:
                        for tname in ("刷新二维码", "更换二维码", "二维码已过期",
                                      "重新获取", "换一张", "扫码登录更便捷"):
                            try:
                                t = page.get_by_text(tname, exact=False).first
                                if t.count() > 0 and t.is_visible():
                                    t.click()
                                    print(f"已点击文本控件: {tname}")
                                    clicked_something = True
                                    break
                            except Exception:
                                continue
                    page.wait_for_timeout(2500)
                page.screenshot(path=args.shot)
                print("已截图:", args.shot)

            # —— 账号密码 / 手机号验证码登录（可选）——
            if args.account or args.phone:
                try:
                    if args.phone:
                        # 1) 切换到手机号验证码登录页签
                        for tname in ("手机号登录", "手机登录", "验证码登录", "短信登录"):
                            t = page.get_by_text(tname, exact=False).first
                            if t.count() > 0 and t.is_visible():
                                t.click()
                                page.wait_for_timeout(800)
                                break
                        # 2) 勾选协议（如存在，不勾会静默登录失败）
                        cb = page.locator('input[type="checkbox"]:visible').first
                        if cb.count() > 0 and not cb.is_checked():
                            cb.check()
                        # 3) 填手机号并发送验证码
                        phone = page.locator(
                            'input[name="phone"], input[type="tel"], '
                            'input[placeholder*="手机"]').first
                        phone.fill(args.phone)
                        send = page.get_by_text("获取验证码").first
                        if send.count() > 0:
                            send.click()
                            print("已点击「获取验证码」，停留 3 秒检测滑块/短信状态 …")
                            page.wait_for_timeout(3000)
                            try:
                                page.screenshot(path="/tmp/leetc_login_status.png")
                            except Exception:
                                print("（截图失败，忽略）")
                            captcha = any(
                                "captcha" in (f.url or "").lower() for f in page.frames
                            ) or "滑块" in (page.content() or "")
                            print("发送验证码后:",
                                  "⚠️ 疑似触发滑块验证码" if captcha else "未发现滑块迹象，短信应已发送")
                        else:
                            print("⚠️ 未找到「获取验证码」按钮，可能页面结构变化")
                        print("已填手机号并点击「获取验证码」，请查收短信。")
                        code = args.code or input("短信验证码: ").strip()
                        code_in = page.locator(
                            'input[name="code"], input[id*="code"], '
                            'input[placeholder*="验证码"]').first
                        code_in.fill(code)
                    else:
                        # 密码登录：切页签 → 填账号密码
                        for tname in ("密码登录", "账号密码登录", "用户登录"):
                            t = page.get_by_text(tname, exact=False).first
                            if t.count() > 0 and t.is_visible():
                                t.click()
                                page.wait_for_timeout(800)
                                break
                        password = args.password or os.environ.get("LEETCODE_PASSWORD")
                        if not password:
                            import getpass
                            password = getpass.getpass("密码（不回显）: ")
                        acc = page.locator(
                            'input[name="login"], #id_login, '
                            'input[placeholder*="账号"], input[placeholder*="邮箱"], '
                            'input[placeholder*="手机"]').first
                        pwd = page.locator(
                            'input[name="password"], #id_password, '
                            'input[type="password"]').first
                        acc.fill(args.account)
                        pwd.fill(password)
                    # 提交登录
                    page.wait_for_timeout(300)
                    btn = page.locator('button[type="submit"]:visible, text=登录').first
                    btn.click()
                    print("已自动填写并提交；若有滑块/图片验证码请手动完成。")
                except Exception as e:
                    print(f"自动填写失败（{type(e).__name__}），请在浏览器里手动完成登录，脚本会继续等待。")

            deadline = time.time() + args.timeout
            found = False
            cookie_map: dict = {}
            while time.time() < deadline:
                cookie_map = {
                    (c.get("name") or ""): (c.get("value") or "")
                    for c in context.cookies()
                }
                if cookie_map.get("LEETCODE_SESSION") and cookie_map.get("csrftoken"):
                    found = True
                    break
                time.sleep(POLL_INTERVAL)

            if not found:
                print(f"[超时] {args.timeout} 秒内未检测到登录。若已登录，")
                print("请确认浏览器地址栏仍停留在 leetcode.cn；也可增大 --timeout 重试。")
                print("（现有 cookie 文件未改动）")
                return 1

            session = cookie_map["LEETCODE_SESSION"]
            csrf = cookie_map["csrftoken"]

            os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump({"LEETCODE_SESSION": session, "csrftoken": csrf}, f)
            os.chmod(COOKIE_FILE, 0o600)

            print(f"✅ 登录成功，cookie 已保存到 {COOKIE_FILE}")
            print(f"   LEETCODE_SESSION: {session[:12]}…（{len(session)} 字符）")
            print(f"   csrftoken: {csrf[:8]}…（{len(csrf)} 字符）")
            print("之后 python leetcode_submit.py --slug <题slug> --file <Solution文件> 会自动读取。")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())