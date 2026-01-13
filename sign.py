import requests
import re
import os
import time
from datetime import datetime

# 配置
MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def wait_until_seven():
    print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}，进入等待模式...")
    while True:
        now = datetime.now()
        # 检查是否到达北京时间早上 7:00 (GitHub 服务器通常是 UTC 时间，注意转换)
        # GitHub Actions 环境通常是 UTC，北京 07:00 = UTC 23:00
        if now.hour == 23 and now.minute == 0:
            print("--- 时间已到，开始抢签！ ---")
            break
        time.sleep(0.5) # 每 0.5 秒检查一次时间

def grab_sign():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }

    # 尝试多次，防止那一秒钟服务器还没开启
    for i in range(10): 
        try:
            # 1. 获取包含动态 sign 的页面
            response = requests.get(SIGN_PAGE, headers=headers, timeout=5)
            match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', response.text)
            
            if match:
                sign_url = BASE_URL + match.group(0)
                # 2. 发起最终签到请求
                res = requests.get(sign_url, headers=headers, timeout=5)
                print(f"第 {i+1} 次尝试签到，目标链接: {sign_url}")
                
                # 简单判断是否成功
                if "已签到" in res.text or "成功" in res.text:
                    print("【成功】抢签成功！")
                    return
            else:
                print(f"第 {i+1} 次尝试：尚未找到签到链接（服务器可能未开启）")
            
        except Exception as e:
            print(f"请求出错: {e}")
        
        time.sleep(1) # 间隔 1 秒重试

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：请先在 GitHub Secrets 中配置 MY_COOKIE")
    else:
        # 第一步：等时间
        wait_until_seven()
        # 第二步：抢签
        grab_sign()
