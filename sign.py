import requests
import re
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 配置
MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def single_shot(i):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }
    try:
        # 增加超时容错，防止网络卡死
        resp = requests.get(SIGN_PAGE, headers=headers, timeout=5)
        # 检查是否真的登录了
        if "登录" in resp.text and "qiandao" not in resp.text:
            print(f"线程[{i}] 警告：Cookie 可能已失效，请更新 Secrets！")
            return "COOKIE_ERROR"
            
        match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', resp.text)
        if match:
            sign_url = BASE_URL + match.group(0)
            res = requests.get(sign_url, headers=headers, timeout=5)
            if "已签到" in res.text or "成功" in res.text:
                print(f"线程[{i}] ★★★ 夺冠成功！时间: {datetime.now().strftime('%H:%M:%S.%f')} ★★★")
                return "SUCCESS"
    except Exception as e:
        pass
    return "RETRY"

def wait_and_sprint():
    # 打印 UTC 和预计的北京时间，方便你对日志
    now = datetime.now()
    print(f"脚本启动时间 (UTC): {now.strftime('%H:%M:%S')}")
    print(f"脚本启动时间 (北京): {(now).strftime('%H:%M:%S')} (注:GitHub环境时间可能不准)")

    # --- 第一阶段：等待 07:00 ---
    while True:
        now = datetime.now()
        # 如果是 06:59:59，进入瞬时爆发
        if now.hour == 22 and now.minute == 59 and now.second == 59:
            time.sleep(0.7)
            print("--- [准点起跑] 已经 06:59:59.700，开始全速冲刺！ ---")
            break
        # 如果启动时已经过 7 点了，直接开始补签
        if now.hour >= 23:
            print(f"--- [补救模式] 检测到启动已迟到 ({now.strftime('%H:%M:%S')})，开始持续轰炸！ ---")
            break
        time.sleep(0.2)

    # --- 第二阶段：长效密集火力网 ---
    # 我们不再只跑 30 次，我们跑 300 次，持续约 60-90 秒
    # 只要这 1 分多钟内论坛开启了签到，你就必中
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(300):
            # 每隔 0.2 秒抛出一个新线程，形成连绵不断的请求压力
            future = executor.submit(single_shot, i)
            # 如果成功了，其实不需要停止，让它把这几十秒跑完最稳
            time.sleep(0.2) 

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未设置环境变量 MY_COOKIE")
    else:
        wait_and_sprint()
