import requests
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ---
TOKEN = "8597164941:AAFooj7wISO14SoP7wTROfAt8kMhcICa6ns"
CHAT_ID = "5444530262"
DATA_FILE = "data.json"
SLEEP_TIME = 3600  # Thời gian nghỉ giữa mỗi lần quét (3600 giây = 1 tiếng)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send(msg):
    print(f"Sending to Telegram: {msg}")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

# ================= TRA CỨU J&T =================
def check_jnt(code):
    code = code.strip().upper()
    try:
        url = f"https://jetapi.jtexpress.vn/track?billcode={code}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=15).json()
        if res.get('data') and len(res['data']) > 0:
            return res['data'][0].get('status', 'Đang xử lý')
        return "Không tìm thấy"
    except:
        return "Lỗi API J&T"

# ================= TRA CỨU SPX (Vượt tường lửa) =================
def check_spx(code):
    code = code.strip().upper() 
    driver = None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_script_timeout(20)
        
        # Truy cập trang chủ lấy Session
        driver.get("https://spx.vn/")
        time.sleep(5) 
        
        # Dùng JS đâm xuyên API
        js_script = f"""
        var callback = arguments[0];
        fetch('https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}')
            .then(res => res.json())
            .then(data => callback(data))
            .catch(err => callback({{"error": true}}));
        """
        data = driver.execute_async_script(js_script)
        
        if data.get("retcode") == 0 and data.get("data") and data["data"].get("tracking_list"):
            latest = data["data"]["tracking_list"][0]
            msg = latest.get("message", "")
            if "giao hàng thành công" in msg.lower() or "đã được giao" in msg.lower():
                return "✅ Đã giao"
            elif "đang giao" in msg.lower():
                return "🚚 Đang giao"
            return f"🔄 {msg}"
        return "Chưa có hành trình mới"
    except Exception as e:
        print(f"Lỗi SPX ({code}): {e}")
        return "SPX đang chặn"
    finally:
        if driver:
            driver.quit()

# ================= VÒNG LẶP CHÍNH =================
def run():
    print("--- BOT BẮT ĐẦU HOẠT ĐỘNG ---")
    while True:
        data = load_data()
        if not data:
            print("Không có đơn hàng nào trong danh sách. Chờ 1 tiếng...")
            time.sleep(SLEEP_TIME)
            continue

        keys_to_delete = []
        
        for code, info in list(data.items()):
            print(f"Đang kiểm tra: {code}...")
            
            if info.get("type") == "jnt":
                status = check_jnt(code)
            else:
                status = check_spx(code)

            # Nếu trạng thái thay đổi thì mới báo
            if status != info.get("last"):
                data[code]["last"] = status
                send(f"📦 Đơn hàng: <b>{code}</b>\n➡ Trạng thái: {status}")
                
                # Nếu đã giao xong thì đánh dấu để xóa
                if status == "✅ Đã giao":
                    keys_to_delete.append(code)
            
            time.sleep(2) # Nghỉ ngắn giữa các đơn tránh bị quét

        # Xóa các đơn đã giao xong khỏi file json
        for k in keys_to_delete:
            print(f"Đã giao xong, xóa đơn {k} khỏi danh sách.")
            del data[k]
        
        save_data(data)
        
        print(f"--- Đã xong lượt. Nghỉ {SLEEP_TIME/60} phút... ---")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    run()
