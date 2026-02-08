import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

MY_COOKIE = (os.environ.get("MY_COOKIE") or "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 你抓到的真实请求就是 qiandao.php?sign=xxxx
SIGN_RE = re.compile(r'qiandao\.php\?sign=([A-Za-z0-9]+)', re.I)

SUCCESS_KWS = ("签到成功", "成功", "今日已签到", "已签到")
LOGIN_KWS = ("请先登录", "登录")

def utc_now():
    return datetime.now(timezone.utc)

def ts():
    return utc_now().strftime("%H:%M:%S.%f")

def headers():
    return {
        "User-Agent": UA,
        "Cookie": MY_COOKIE,
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

def get(session: requests.Session, url: str):
    return session.get(url, headers=headers(), timeout=10, allow_redirects=True)

def wait_until_beijing_0700_strict():
    """
    北京时间 07:00:00 == UTC 23:00:00（前一天）
    严格：07:00 前不访问签到页、不请求 sign。
    """
    now = utc_now()
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    print(f"[INFO] start utc={ts()} cookie_len={len(MY_COOKIE)} target_utc={target.strftime('%H:%M:%S')}")

    if now >= target:
        print(f"[INFO] already past 07:00(BJT) -> start now utc={ts()}")
        return

    while True:
        now = utc_now()
        if now >= target:
            print(f"[INFO] reached 07:00(BJT) utc={ts()} -> start requests")
            return

        if now.second % 20 == 0:
            remain = (target - now).total_seconds()
            print(f"[WAIT] utc={ts()} remain={remain:.1f}s")
            time.sleep(1)

        time.sleep(0.2)

def try_once(session: requests.Session):
    """
    单次尝试：GET qiandao.php -> 抓 sign -> GET qiandao.php?sign=xxx
    """
    r = get(session, SIGN_PAGE)
    print(f"[HTTP] SIGN_PAGE {r.status_code} {r.url}")
    text = r.text or ""

    if any(k in text for k in LOGIN_KWS):
        return "COOKIE_ERROR", "login keywords detected"

    if "今日已签到" in text or "已签到" in text:
        return "ALREADY", "already signed"

    m = SIGN_RE.search(text)
    if not m:
        # 给一点片段用于判断页面是否变了/被拦
        snippet = text[:300].replace("\n", " ") if text else ""
        return "NO_SIGN", f"no sign found. head={snippet!r}"

    sign = m.group(1)
    sign_url = f"{SIGN_PAGE}?sign={sign}"
    rr = get(session, sign_url)
    print(f"[HTTP] SIGN_GET  {rr.status_code} {rr.url}")
    body = rr.text or ""

    if any(k in body for k in SUCCESS_KWS):
        return "OK", "signed"

    snippet = body[:250].replace("\n", " ") if body else ""
    return "FAIL", f"not success. head={snippet!r}"

def phase(session, label, attempts, interval):
    print(f"[PHASE] {label} utc={ts()} attempts={attempts} interval={interval}s")
    for i in range(1, attempts + 1):
        status, detail = try_once(session)
        print(f"[RESULT] {label} #{i} status={status} detail={detail}")
        if status in ("OK", "ALREADY"):
            print(f"[DONE] {status} utc={ts()}")
            return 0
        if status == "COOKIE_ERROR":
            print("[FATAL] cookie invalid / not logged in")
            return 3
        time.sleep(interval)
    return 1

def main():
    if not MY_COOKIE:
        print("[FATAL] MY_COOKIE 未设置")
        return 2

    # 07:00 前不做任何请求
    wait_until_beijing_0700_strict()

    s = requests.Session()

    # 主窗口：短间隔尝试（例如 10 次，每 0.8 秒一次，总共约 8 秒）
    rc = phase(s, "MAIN", attempts=10, interval=0.8)
    if rc in (0, 3):
        return rc

    # 补签：低频尝试（例如 12 次，每 25 秒一次，约 5 分钟）
    rc2 = phase(s, "MAKEUP", attempts=12, interval=25)
    return rc2

if __name__ == "__main__":
    sys.exit(main())
