import requests
import json
import time
import datetime  # Thêm thư viện này để xử lý ngày giờ
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ---
TOKEN = "8597164941:AAFooj7wISO14SoP7wTROfAt8kMhcICa6ns"
CHAT_ID = "5444530262"
DATA_FILE = "data.json"
SLEEP_TIME = 7200  # Quét 2 tiếng / lần

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
    print(f"Sending to Telegram...\n")
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

# ================= TRA CỨU SPX (LẤY FULL HÀNH TRÌNH) =================
def check_spx(code):
    code = code.strip().upper() 
    driver = None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Đường dẫn Chrome trong Docker
        options.binary_location = "/usr/bin/chromium"
        
        # Các lệnh tàng hình
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        driver.set_script_timeout(30)
        print(f"--- ĐANG MỞ CHROME KIỂM TRA: {code} ---")
        driver.get("https://spx.vn/")
        time.sleep(10) 
        
        js_script = f"""
        var callback = arguments[0];
        fetch('https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}')
            .then(res => res.json())
            .then(data => callback(data))
            .catch(err => callback({{"error": true}}));
        """
        data = driver.execute_async_script(js_script)
        
        if "error" in data:
            return "SPX chặn kết nối (Error Fetch)"

        if data.get("retcode") == 0 and data.get("data") and data["data"].get("tracking_list"):
            tracking_list = data["data"]["tracking_list"]
            
            # 1. Xác định trạng thái chính từ dòng mới nhất (để hiển thị tiêu đề)
            latest_msg = tracking_list[0].get("message", "").lower()
            if "giao hàng thành công" in latest_msg or "đã được giao" in latest_msg:
                main_status = "✅ Đã giao"
            elif "đang giao" in latest_msg:
                main_status = "🚚 Đang giao"
            else:
                main_status = "🔄 Đang vận chuyển"

            # 2. Vòng lặp lấy TOÀN BỘ hành trình
            journey_lines = []
            for item in tracking_list:
                msg = item.get("message", "")
                timestamp = item.get("timestamp")
                time_str = ""
                if timestamp:
                    try:
                        # Xử lý thời gian (Shopee thường dùng epoch time)
                        if timestamp > 20000000000:
                            timestamp = timestamp / 1000
                        dt = datetime.datetime.fromtimestamp(timestamp)
                        time_str = dt.strftime('%d/%m %H:%M') + " - " # Ví dụ: 08/04 22:34 - 
                    except:
                        pass
                journey_lines.append(f"• {time_str}{msg}")
            
            # Gộp tất cả các dòng lại thành 1 đoạn văn bản
            full_journey = "\n".join(journey_lines)
            
            # Trả về Tiêu đề + Toàn bộ hành trình
            return f"{main_status}\n{full_journey}"
            
        return "Chưa có hành trình mới"
    except Exception as e:
        print(f"Lỗi SPX ({code}): {str(e)}")
        return f"SPX đang chặn (Lỗi hệ thống)"
    finally:
        if driver:
            driver.quit()

# ================= VÒNG LẶP CHÍNH =================
def run():
    print("--- BOT BẮT ĐẦU HOẠT ĐỘNG ---")
    while True:
        data = load_data()
        if not data:
            print("Không có đơn hàng nào trong danh sách. Chờ 2 tiếng...")
            time.sleep(SLEEP_TIME)
            continue

        keys_to_delete = []
        
        for code, info in list(data.items()):
            print(f"Đang kiểm tra: {code}...")
            
            if info.get("type") == "jnt":
                status = check_jnt(code)
            else:
                status = check_spx(code)

            if status != info.get("last"):
                # Cập nhật trạng thái mới
                data[code]["last"] = status
                send(f"📦 Đơn hàng: <b>{code}</b>\n➡ Trạng thái: {status}")
                
                # CHÚ Ý: Đã sửa lại logic xóa đơn. Vì 'status' giờ là 1 đoạn rất dài, 
                # nên ta dùng 'in' để kiểm tra xem có chữ "Đã giao" trong đoạn đó không.
                if "✅ Đã giao" in status:
                    keys_to_delete.append(code)
            
            time.sleep(5) 

        for k in keys_to_delete:
            del data[k]
        save_data(data)
        
        print(f"--- Đã xong lượt. Nghỉ {SLEEP_TIME/60} phút... ---")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    run()
