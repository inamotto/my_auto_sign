import requests
import re
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor # 导入多线程库

# 配置
MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def single_shot(i):
    """单个请求任务：尝试刷新并签到"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }
    try:
        # 1. 尝试获取 sign
        resp = requests.get(SIGN_PAGE, headers=headers, timeout=3)
        match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', resp.text)
        if match:
            sign_url = BASE_URL + match.group(0)
            # 2. 发现 sign 立即请求签到
            res = requests.get(sign_url, headers=headers, timeout=3)
            if "已签到" in res.text or "成功" in res.text:
                print(f"线程[{i}] 夺冠成功！时间: {datetime.now().strftime('%H:%M:%S.%f')}")
                return True
    except:
        pass
    return False

def wait_and_sprint():
    print(f"脚本已启动，当前时间: {datetime.now().strftime('%H:%M:%S')}，正在监听 07:00:00...")
    
    while True:
        now = datetime.now()
        # 还没到 23:00 (北京 07:00)
        if now.hour < 23:
            if now.hour == 22 and now.minute == 59 and now.second == 59:
                time.sleep(0.8) 
                print("--- [准点爆发] ---")
                break
            time.sleep(0.5)
        # 已经过了 23:00 (北京 07:00)
        else:
            print(f"检测到时间已过 ({now.strftime('%H:%M:%S')})，进入持续补签模式...")
            break

    # 关键修改：增加持续时间，即使迟到也要死磕到底
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 将任务增加到 200 次，确保即使服务器反应慢，我们也能持续轰炸 20-30 秒
        for i in range(200): 
            executor.submit(single_shot, i)
            # 每次请求间隔稍微拉开一点，形成持续火力
            time.sleep(0.2) 
    
    print("所有尝试已结束。")

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未设置 Cookie")
    else:
        wait_and_sprint()
