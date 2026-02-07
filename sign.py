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
        # 增加超时容错
        resp = requests.get(SIGN_PAGE, headers=headers, timeout=5)
        # 登录校验
        if "登录" in resp.text and "qiandao" not in resp.text:
            return "COOKIE_ERROR"
            
        # 提取动态签到参数
        match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', resp.text)
        if match:
            sign_url = BASE_URL + match.group(0)
            res = requests.get(sign_url, headers=headers, timeout=5)
            if "已签到" in res.text or "成功" in res.text:
                print(f"线程[{i}] ★★★ 签到成功！时间: {datetime.now().strftime('%H:%M:%S.%f')} ★★★")
                return "SUCCESS"
    except Exception:
        pass
    return "RETRY"

def wait_and_sprint():
    print(f"脚本启动，当前时间 (UTC): {datetime.now().strftime('%H:%M:%S')}")
    
    # --- 第一阶段：静默等待与存活报告 ---
    while True:
        now = datetime.now()
        # 北京时间 07:00:00 是 UTC 23:00:00
        # 脚本在 22:59:58 提前 2 秒进入战斗状态
        if now.hour == 22 and now.minute == 59 and now.second >= 58:
            print(f"--- [时刻已到: {now.strftime('%H:%M:%S')}] 准备进入火力网 ---")
            break
        
        if now.hour >= 23:
            print(f"--- [检测到已过点: {now.strftime('%H:%M:%S')}] 直接补签 ---")
            break
            
        # 存活报告：每 30 秒打印一次，防止被 GitHub 判定为僵尸进程
        if now.second % 30 == 0:
            print(f"等待中... 当前时刻 (UTC): {now.strftime('%H:%M:%S')}")
            time.sleep(1) # 避免在一秒内重复触发打印
        
        time.sleep(0.5)

    # --- 第二阶段：密集火力轰炸 ---
    print("开始执行 300 次并发冲刺...")
    # 使用线程池，模拟多路并发
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(300):
            executor.submit(single_shot, i)
            # 每 0.1 秒发射一枚“导弹”
            time.sleep(0.1) 
    
    print(f"冲刺结束，最终时间: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未设置环境变量 MY_COOKIE")
    else:
        wait_and_sprint()
