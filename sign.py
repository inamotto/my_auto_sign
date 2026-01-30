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
    print(f"脚本已于 {datetime.now().strftime('%H:%M:%S')} 成功抢占服务器，准备长效守候...")
    
    # --- 第一阶段：长效守候与保活 ---
    while True:
        now = datetime.now()
        # 北京 07:00 对应 UTC 23:00
        
        # 1. 还没到 7 点（23点 UTC）
        if now.hour == 22:
            # 每 5 分钟打印一次日志，告诉 GitHub 脚本还活着，防止被自动关闭
            if now.second == 0 and now.minute % 5 == 0:
                print(f"正在守候中... 当前北京时间: 06:{now.minute:02d}，请放心，脚本在线。")
                time.sleep(1) 
            
            # 到达 06:59:59，进入冲刺准备
            if now.minute == 59 and now.second == 59:
                print("--- [关键时刻] 06:59:59 已到，开始毫秒级秒杀！ ---")
                break
        
        # 2. 如果排队太久，进场时已经过 7 点了（23点 UTC）
        elif now.hour >= 23:
            print(f"检测到时间已过 07:00 ({now.strftime('%H:%M:%S')})，立即开始补签冲刺！")
            break
            
        time.sleep(0.5) # 低频对时，节省资源

    # --- 第二阶段：毫秒级冲刺（这部分保持原样，非常高效） ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }

    print("开始毫秒级轮询页面...")
    for i in range(25):  # 稍微增加次数到 25 次，确保覆盖前几秒波动
        try:
            response = requests.get(SIGN_PAGE, headers=headers, timeout=5)
            match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', response.text)
            
            if match:
                sign_url = BASE_URL + match.group(0)
                res = requests.get(sign_url, headers=headers, timeout=5)
                if "已签到" in res.text or "成功" in res.text:
                    print(f"【夺冠】签到成功！完成时间点: {datetime.now().strftime('%H:%M:%S.%f')}")
                    return
                else:
                    print(f"尝试第 {i+1} 次：捕获到链接但签到未成功，重试中...")
            # 如果没找到 sign，不打印，避免日志太乱，直接进行下一次尝试
                
        except Exception as e:
            print(f"冲刺异常: {e}")
        
        time.sleep(0.1) # 0.1秒刷新一次

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：GitHub Secrets 中未设置 MY_COOKIE")
    else:
        wait_and_sprint()
