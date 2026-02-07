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
    print(f"脚本启动，当前时间: {datetime.now().strftime('%H:%M:%S')}")
    
    while True:
        now = datetime.now()
        # 北京时间 07:00:00 对应 UTC 23:00:00
        # 只要还没到 22:59:58，我们就每 10 秒打个卡，防止被 GitHub 熔断
        if now.hour == 22 and now.minute == 59 and now.second >= 58:
            print("--- [倒计时 2 秒] 准备进入火力网 ---")
            break
        
        # 如果已经过点了，直接开始
        if now.hour >= 23:
            print("--- [检测到已过点] 直接补签 ---")
            break
            
        # 存活报告：每 30 秒打印一次，防止被判定为僵尸进程
        if now.second % 30 == 0:
            print(f"等待中... 当前时刻: {now.strftime('%H:%M:%S')}")
            time.sleep(1) 
        
        time.sleep(0.5)

    # 冲刺阶段... (保持之前的 ThreadPoolExecutor 逻辑)

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未设置环境变量 MY_COOKIE")
    else:
        wait_and_sprint()
