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
    print(f"脚本已启动，正在监听 07:00:00...")
    
    while True:
        now = datetime.now()
        # 北京 07:00 对应 UTC 23:00
        if now.hour == 22 and now.minute == 59 and now.second == 59:
            # 提前 100 毫秒左右进入爆发状态
            time.sleep(0.8) 
            print("--- [全火力爆发] 06:59:59.800，开始多线程并发刷新！ ---")
            break
        if now.hour == 23:
            print("检测到时间已过，执行补签...")
            break
        time.sleep(0.1)

    # 使用线程池并发发起 10 个请求，不再一个一个排队
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 同时提交 30 个冲刺任务，谁快谁赢
        for i in range(30):
            executor.submit(single_shot, i)
            # 每次提交任务间隔极短，形成密集的请求雨
            time.sleep(0.05) 

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未设置 Cookie")
    else:
        wait_and_sprint()
