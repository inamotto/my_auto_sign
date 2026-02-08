import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"
MY_COOKIE = (os.environ.get("MY_COOKIE") or "").strip()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SIGN_RE = re.compile(r'qiandao\.php\?[^"\']*sign=([A-Za-z0-9_%-]+)', re.I)
FORMHASH_RE = re.compile(r'name="formhash"\s+value="([a-z0-9]+)"', re.I)

SUCCESS_KWS = ("签到成功", "成功", "已签到", "今日已签到")
LOGIN_KWS = ("请先登录", "登录")

def now_utc():
    return datetime.now(timezone.utc)

def fmt(dt):
    return dt.strftime("%H:%M:%S.%f")

def headers():
    return {
        "User-Agent": UA,
        "Cookie": MY_COOKIE,
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

def get(session, url):
    return session.get(url, headers=headers(), timeout=10, allow_redirects=True)

def post(session, url, data):
    h = headers().copy()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return session.post(url, headers=h, data=data, timeout=10, allow_redirects=True)

def beijing_target_0700_utc_dt():
    # 北京时间 = UTC+8；07:00 北京 = 23:00 UTC（前一天）
    # 这里以“当前 UTC 日期”为基准算出最近的目标 23:00:00
    now = now_utc()
    # 目标小时=23:00:00 UTC
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    # 如果现在已经过了 23:00 UTC，就表示今天的 07:00 已过，目标不再等待
    return target

def wait_until_0700_beijing_strict():
    """
    严格保证：07:00（北京时间）之前不发签到请求。
    仅等待+心跳日志。
    """
    target = beijing_target_0700_utc_dt()
    now = now_utc()

    print(f"[INFO] start utc={fmt(now)} cookie_len={len(MY_COOKIE)}")
    print(f"[INFO] target(UTC)={fmt(target)}  (== 北京 07:00)")

    if now >= target:
        print(f"[INFO] already past target utc={fmt(now)} -> no wait")
        return

    while True:
        now = now_utc()
        if now >= target:
            print(f"[INFO] reached target utc={fmt(now)} -> start requests")
            return

        # 心跳：每 20 秒一次
        if now.second % 20 == 0:
            remain = (target - now).total_seconds()
            print(f"[WAIT] utc={fmt(now)} remain={remain:.1f}s")
            time.sleep(1)

        time.sleep(0.2)

def try_checkin(session):
    """
    单次尝试：先访问签到页判断已签到/登录态，再走 GET sign 或 POST formhash
    """
    r = get(session, SIGN_PAGE)
    print(f"[HTTP] SIGN_PAGE {r.status_code} {r.url}")
    text = r.text or ""

    if any(k in text for k in LOGIN_KWS):
        return "COOKIE_ERROR", "login keywords detected"

    if "今日已签到" in text or "已签到" in text:
        return "ALREADY", "already signed"

    m = SIGN_RE.search(text)
    if m:
        sign_url = SIGN_PAGE + "?sign=" + m.group(1)
        rr = get(session, sign_url)
        print(f"[HTTP] SIGN_GET  {rr.status_code} {rr.url}")
        body = rr.text or ""
        if any(k in body for k in SUCCESS_KWS):
            return "OK", "GET sign success"
        return "FAIL", f"GET not success head={body[:200]!r}"

    fm = FORMHASH_RE.search(text)
    if fm:
        data = {
            "formhash": fm.group(1),
            "qdmode": "1",
            "todaysay": "",
            "fastreply": "0",
        }
        rr = post(session, SIGN_PAGE, data)
        print(f"[HTTP] SIGN_POST {rr.status_code} {rr.url}")
        body = rr.text or ""
        if any(k in body for k in SUCCESS_KWS):
            return "OK", "POST formhash success"
        return "FAIL", f"POST not success head={body[:200]!r}"

    # 说明按钮可能是 XHR/JS
    return "FAIL", "no sign link / no formhash (maybe XHR/JS button)"

def phase(session, label, attempts, interval):
    print(f"[PHASE] {label} utc={fmt(now_utc())} attempts={attempts} interval={interval}s")
    for i in range(1, attempts + 1):
        status, detail = try_checkin(session)
        print(f"[RESULT] {label} #{i} status={status} detail={detail}")
        if status in ("OK", "ALREADY"):
            print(f"[DONE] {status} utc={fmt(now_utc())}")
            return 0
        if status == "COOKIE_ERROR":
            return 3
        time.sleep(interval)
    return 1

def main():
    if not MY_COOKIE:
        print("[FATAL] MY_COOKIE 未设置")
        return 2

    # 严格：07:00 之前不发请求
    wait_until_0700_beijing_strict()

    s = requests.Session()

    # 主签窗口：短间隔（例如 10 次，0.8s），总计约 8 秒
    rc = phase(s, "MAIN", attempts=10, interval=0.8)
    if rc in (0, 3):
        return rc

    # 补签窗口：低频（例如 12 次，每 25 秒一次），总计约 5 分钟
    # 注意：你也可以把补签放到 workflow 的 07:05/07:15/07:30 run 去做
    rc2 = phase(s, "MAKEUP", attempts=12, interval=25)
    return rc2

if __name__ == "__main__":
    sys.exit(main())
