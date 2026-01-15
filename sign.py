import requests
import re
import os
import time
import random
from datetime import datetime

# 配置
MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def wait_until_seven():
    print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}，进入等待模式...")
    while True:
        now = datetime.now()
        # GitHub Actions 通常使用 UTC 时间，北京 07:00 = UTC 23:00
        # 如果你的日志显示服务器时间就是北京时间，请将 23 改为 7
        if now.hour == 23 and now.minute == 0:
            # --- 新增随机延迟逻辑 ---
            # 在 2.0 秒到 5.0 秒之间随机选择一个时间点
            delay = round(random.uniform(2.0, 5.0), 2)
            print(f"--- 时间已到！模拟真人操作，随机等待 {delay} 秒后发起冲刺 ---")
            time.sleep(delay)
            break
        time.sleep(0.5)

def grab_sign():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }

    # 尝试多轮，增加成功率
    for i in range(5): 
        try:
            response = requests.get(SIGN_PAGE, headers=headers, timeout=10)
            # 这里的正则关联了你之前检查出来的 href="qiandao.php?sign=xxxx"
            match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', response.text)
            
            if match:
                sign_url = BASE_URL + match.group(0)
                print(f"第 {i+1} 次尝试，目标地址: {sign_url}")
                
                res = requests.get(sign_url, headers=headers, timeout=10)
                if "已签到" in res.text or "成功" in res.text:
                    print(f"【成功】抢签成功！触发时间: {datetime.now().strftime('%H:%M:%S')}")
                    return
            else:
                print(f"第 {i+1} 次尝试：尚未获取到签到 sign，服务器可能还在处理零点任务...")
            
        except Exception as e:
            print(f"请求过程中出现异常: {e}")
        
        time.sleep(1.5) # 每轮之间稍作停顿

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未在 GitHub Secrets 中找到 MY_COOKIE")
    else:
        wait_until_seven()
        grab_sign()
