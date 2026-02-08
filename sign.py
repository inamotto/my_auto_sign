import os
import re
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

MY_COOKIE = os.environ.get("MY_COOKIE", "").strip()

BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SUCCESS_KWS = ("签到成功", "成功", "已签到", "签到完成")
FAIL_KWS = ("权限", "失败", "请先登录", "登录", "验证码", "过于频繁", "Forbidden", "Cloudflare", "Access Denied")

# 更宽松的 token 抓取：允许大写/下划线/百分号等
SIGN_RE = re.compile(r'qiandao\.php\?[^"\']*sign=([A-Za-z0-9_%-]+)', re.I)

def now_utc_str():
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")

def build_session():
    s = requests.Session()
    # 连接池更稳一点
    adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=0)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def headers():
    return {
        "User-Agent": UA,
        "Cookie": MY_COOKIE,
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

def single_shot(i: int) -> str:
    s = build_session()
    h = headers()

    try:
        # 1) 访问签到页拿 token
        resp = s.get(SIGN_PAGE, headers=h, timeout=8, allow_redirects=True)
        code = resp.status_code
        final_url = resp.url

        # 关键诊断：偶尔打印一下即可（避免日志爆炸）
        if i in (0, 1, 2, 10, 50, 100):
            print(f"[{now_utc_str()}] [{i}] SIGN_PAGE status={code} url={final_url}")

        text = resp.text or ""

        # 简单判断登录态（这只是提示，不是绝对）
        if ("登录" in text or "请先登录" in text) and ("qiandao" not in text):
            return "COOKIE_ERROR"

        # 如果页面本身就提示已签到
        if any(k in text for k in SUCCESS_KWS):
            print(f"[{now_utc_str()}] [{i}] ★ 已经处于已签到状态（在签到页检测到）")
            return "ALREADY"

        m = SIGN_RE.search(text)
        if not m:
            # 打印一小段与 qiandao/sign 相关的上下文，便于你判断页面结构是否变了/被拦
            idx = text.lower().find("qiandao")
            snippet = text[idx:idx+400] if idx != -1 else text[:400]
            print(f"[{now_utc_str()}] [{i}] NO_TOKEN. status={code}. snippet={snippet!r}")
            # 常见被拦：403/503
            if code in (403, 429, 503):
                return "BLOCKED"
            return "NO_TOKEN"

        sign_token = m.group(1)
        sign_url = f"{SIGN_PAGE}?sign={sign_token}"

        # 2) 发起签到请求
        res = s.get(sign_url, headers=h, timeout=8, allow_redirects=True)
        rcode = res.status_code
        rtext = res.text or ""

        if any(k in rtext for k in SUCCESS_KWS):
            print(f"[{now_utc_str()}] [{i}] ★★★ 签到命中！ status={rcode} ★★★")
            return "SUCCESS"

        # 如果疑似失败原因，挑一个打印出来
        hit_fail = next((k for k in FAIL_KWS if k in rtext), None)
        if i in (0, 1, 2, 10, 50, 100) or hit_fail:
            print(f"[{now_utc_str()}] [{i}] SIGN_RES status={rcode} hit_fail={hit_fail} head={rtext[:200]!r}")

        if rcode in (403, 429, 503):
            return "BLOCKED"

        return "RETRY"

    except Exception as e:
        # 不要吞异常
        print(f"[{now_utc_str()}] [{i}] EXCEPTION: {type(e).__name__}: {e}")
        return "EXCEPTION"


def wait_until_target():
    # 你原来的目标：UTC 22:59:58 进入冲刺（= 北京 06:59:58）
    print(f"脚本启动，当前时间(UTC): {now_utc_str()}")
    while True:
        now = datetime.now(timezone.utc)
        if now.hour == 22 and now.minute == 59 and now.second >= 58:
            print(f"--- [到点: {now_utc_str()}] 进入冲刺 ---")
            return
        if now.hour >= 23:
            print(f"--- [已过点: {now_utc_str()}] 直接补签冲刺 ---")
            return

        # 存活报告：每 30 秒
        if now.second % 30 == 0:
            print(f"等待中... 当前(UTC): {now_utc_str()}")
            time.sleep(1)
        time.sleep(0.3)


def main():
    if not MY_COOKIE:
        print("错误：未设置环境变量 MY_COOKIE")
        return

    wait_until_target()

    # 冲刺参数：不要太夸张，否则容易触发频控/封禁
    total = 200
    max_workers = 12
    interval = 0.08

    print(f"开始并发冲刺：total={total}, workers={max_workers}, interval={interval}s")

    stats = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = []
        for i in range(total):
            futures.append(ex.submit(single_shot, i))
            time.sleep(interval)

        for f in as_completed(futures):
            r = f.result()
            stats[r] = stats.get(r, 0) + 1

    print(f"冲刺结束(UTC): {now_utc_str()} 结果统计: {stats}")

    # 让 workflow 用退出码体现失败（可选）
    if stats.get("SUCCESS", 0) == 0 and stats.get("ALREADY", 0) == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
