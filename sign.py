import requests
import re
import os
import time
from datetime import datetime

# 配置
MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def wait_and_sprint():
    print(f"脚本启动时间: {datetime.now().strftime('%H:%M:%S')}，正在等待 07:00:00...")
    
    # --- 第一阶段：精准守候 ---
    while True:
        now = datetime.now()
        # 北京 07:00 对应 UTC 23:00
        # 当时间到达 06:59:59 时，立即结束等待，进入冲刺
        if now.hour == 22 and now.minute == 59 and now.second == 59:
            print("--- [关键时刻] 06:59:59 已到，准备进入毫秒级秒杀！ ---")
            break
        
        # 如果排队导致启动太晚（比如已经 07:00:01 了），直接冲刺
        if now.hour == 23:
            print("检测到时间已过 07:00，立即开始补签冲刺！")
            break
            
        time.sleep(0.1) # 高频对时

    # --- 第二阶段：高频刷新冲刺 ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }

    print("开始毫秒级轮询页面...")
    # 连续循环，模拟疯狂点击刷新按钮
    for i in range(20):  # 增加到20次，覆盖前3-5秒的黄金时间
        try:
            # 1. 访问签到页面（相当于刷新页面）
            response = requests.get(SIGN_PAGE, headers=headers, timeout=5)
            # 2. 寻找最新的签到令牌 sign
            match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', response.text)
            
            if match:
                sign_url = BASE_URL + match.group(0)
                # 3. 立即点击签到链接
                res = requests.get(sign_url, headers=headers, timeout=5)
                if "已签到" in res.text or "成功" in res.text:
                    print(f"【夺冠】签到成功！完成时间点: {datetime.now().strftime('%H:%M:%S.%f')}")
                    return
                else:
                    print(f"尝试第 {i+1} 次：捕获到链接但签到未成功，重试中...")
            else:
                # 如果没找到 sign，说明服务器还没放开 07:00 的签到口
                pass 
                
        except Exception as e:
            print(f"冲刺异常: {e}")
        
        # 极短间隔：0.1秒刷新一次。这是“抢第一”的关键。
        time.sleep(0.1)

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：GitHub Secrets 中未设置 MY_COOKIE")
    else:
        wait_and_sprint()
