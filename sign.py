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

# 你抓到的真实请求：GET qiandao.php?sign=xxxx
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


def target_utc_for_beijing_0700():
    """
    北京时间 07:00:00 == UTC 23:00:00（同一个“北京时间日”的前一天 UTC）
    - 如果现在还没到 UTC 23:00：就等到今天 UTC 23:00
    - 如果现在已经过了 UTC 23:00：说明北京时间 07:00 已过，直接开始（用于补签触发）
    """
    now = utc_now()
    target = now.replace(hour=23, minute=0, second=0, microsecond=0)
    return target


def fetch_sign_from_page(html: str):
    m = SIGN_RE.search(html or "")
    return m.group(1) if m else None


def preload_sign_then_wait_fire(session: requests.Session):
    """
    准点策略：
    - 06:59:55(北京) ≈ UTC 22:59:55：先 GET 一次 SIGN_PAGE 预取 sign（不发签到请求）
    - 07:00:00(北京) ≈ UTC 23:00:00：立刻用 sign 发签到请求
    若现在已经过点：不等待，直接返回 None（后续走正常 try_once 逻辑）
    """
    now = utc_now()
    target = target_utc_for_beijing_0700()

    print(f"[INFO] start utc={ts()} cookie_len={len(MY_COOKIE)} target_utc={target.strftime('%H:%M:%S')}")

    if now >= target:
        print(f"[INFO] already past 07:00(BJT) utc={ts()} -> no preload wait")
        return None

    preload_at = target - timedelta(seconds=5)  # 北京 06:59:55
    sign_value = None

    while True:
        now = utc_now()

        # 心跳
        if now.second % 20 == 0:
            remain = (target - now).total_seconds()
            print(f"[WAIT] utc={ts()} remain={remain:.1f}s")
            time.sleep(1)

        # 到预取时间：只访问签到页（不访问 sign 链接）
        if sign_value is None and now >= preload_at:
            print(f"[PRELOAD] utc={ts()} GET {SIGN_PAGE}")
            r = get(session, SIGN_PAGE)
            print(f"[HTTP] PRELOAD_PAGE {r.status_code} {r.url}")

            text = r.text or ""
            if any(k in text for k in LOGIN_KWS):
                print("[FATAL] cookie invalid / not logged in (during preload)")
                return "COOKIE_ERROR"

            # 预取 sign（可能预取不到；预取到也可能 07:00 才生效）
            sign_value = fetch_sign_from_page(text)
            print(f"[PRELOAD] sign={'(none)' if not sign_value else sign_value}")

        # 到点：开火
        if now >= target:
            print(f"[FIRE] utc={ts()} -> fire sign request")
            return sign_value

        time.sleep(0.1)


def try_sign_with_value(session: requests.Session, sign_value: str):
    """
    用给定的 sign 直接发签到请求（这是“点击按钮”的那个 GET）
    """
    sign_url = f"{SIGN_PAGE}?sign={sign_value}"
    rr = get(session, sign_url)
    print(f"[HTTP] SIGN_GET  {rr.status_code} {rr.url}")
    body = rr.text or ""
    if any(k in body for k in SUCCESS_KWS):
        return "OK", "signed"
    snippet = body[:250].replace("\n", " ") if body else ""
    return "FAIL", f"not success. head={snippet!r}"


def try_once(session: requests.Session):
    """
    单次尝试（常规流程）：
    GET SIGN_PAGE -> 判断登录/已签到 -> 抓 sign -> GET sign
    """
    r = get(session, SIGN_PAGE)
    print(f"[HTTP] SIGN_PAGE {r.status_code} {r.url}")
    text = r.text or ""

    if any(k in text for k in LOGIN_KWS):
        return "COOKIE_ERROR", "login keywords detected"

    if "今日已签到" in text or "已签到" in text:
        return "ALREADY", "already signed"

    sign_value = fetch_sign_from_page(text)
    if not sign_value:
        snippet = text[:300].replace("\n", " ") if text else ""
        return "NO_SIGN", f"no sign found. head={snippet!r}"

    return try_sign_with_value(session, sign_value)


def phase(session: requests.Session, label: str, attempts: int, interval: float):
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

    s = requests.Session()

    # --- 准点策略：06:59:55 预取 sign，07:00:00 直接发 sign 请求 ---
    preload_result = preload_sign_then_wait_fire()

    if preload_result == "COOKIE_ERROR":
        return 3

    if isinstance(preload_result, str) and preload_result:
        # 有预取 sign：先用它打第一枪（最快）
        status, detail = try_sign_with_value(s, preload_result)
        print(f"[RESULT] PRELOAD_FIRE status={status} detail={detail}")

        if status in ("OK", "ALREADY"):
            print(f"[DONE] {status} utc={ts()}")
            return 0

        # 预取 sign 可能在 07:00 前生成但 07:00 才生效，也可能根本无效
        # 失败后立刻走一次常规流程（07:00 后重新抓 sign 再打），避免错过
        print("[INFO] preload sign failed -> immediate normal retry")
        status2, detail2 = try_once()
        print(f"[RESULT] IMMEDIATE_RETRY status={status2} detail={detail2}")
        if status2 in ("OK", "ALREADY"):
            print(f"[DONE] {status2} utc={ts()}")
            return 0
        if status2 == "COOKIE_ERROR":
            return 3

    else:
        # 没预取（比如已经过点/或者预取没抓到 sign）：直接进入主流程
        print("[INFO] no preload sign -> enter normal flow")

    # --- 主窗口：短间隔（用于 07:00 附近快速抢）---
    rc = phase(s, "MAIN", attempts=10, interval=0.8)
    if rc in (0, 3):
        return rc

    # --- 补签：低频，避免太激进 ---
    rc2 = phase(s, "MAKEUP", attempts=12, interval=25)
    return rc2


if __name__ == "__main__":
    sys.exit(main())
