import requests
import re
import os
import time
import random
from datetime import datetime

MY_COOKIE = os.environ.get('MY_COOKIE')
BASE_URL = "https://bbs.xudashi.cn/"
SIGN_PAGE = BASE_URL + "qiandao.php"

def wait_until_seven():
    print(f"脚本启动时间: {datetime.now().strftime('%H:%M:%S')}，开始逻辑判断...")
    while True:
        now = datetime.now()
        # 北京 07:00 对应 UTC 23:00
        # 逻辑：如果是 06:45 到 06:59 之间启动的，就等
        if now.hour == 22 and now.minute >= 45:
            if now.minute == 59 and now.second == 59:
                delay = round(random.uniform(2.0, 5.0), 2)
                print(f"准点守候成功！随机延迟 {delay} 秒后抢签...")
                time.sleep(delay)
                break
            time.sleep(0.1) # 高频对时
        
        # 逻辑：如果脚本启动时已经是 07:00 之后了（比如 07:16 延迟启动）
        elif (now.hour == 23 and now.minute <= 30) or (now.hour == 22 and now.minute >= 59):
            print("检测到时间已过或延迟启动，不再等待，立即补签！")
            break
            
        else:
            print("当前不在签到时间窗口，为防止超时被封，脚本直接退出。")
            exit(0)

def grab_sign():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': MY_COOKIE,
        'Referer': BASE_URL
    }
    for i in range(5):
        try:
            # 实时获取页面上的 sign 动态参数
            response = requests.get(SIGN_PAGE, headers=headers, timeout=10)
            match = re.search(r'qiandao\.php\?sign=([a-z0-9]+)', response.text)
            if match:
                sign_url = BASE_URL + match.group(0)
                print(f"尝试请求: {sign_url}")
                res = requests.get(sign_url, headers=headers, timeout=10)
                if "已签到" in res.text or "成功" in res.text:
                    print(f"【成功】签到已完成！时间: {datetime.now().strftime('%H:%M:%S')}")
                    return
            else:
                print(f"未找到 sign (第{i+1}次)，可能服务器未开启签到。")
        except Exception as e:
            print(f"请求报错: {e}")
        time.sleep(2)

if __name__ == "__main__":
    if not MY_COOKIE:
        print("错误：未检测到 Cookie 变量")
    else:
        wait_until_seven()
        grab_sign()
