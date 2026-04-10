import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TOKEN = "8597164941:AAFooj7wISO14SoP7wTROfAt8kMhcICa6ns"
CHAT_ID = "5444530262"
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

# ================= J&T =================
def check_jnt(code):
    code = code.strip().upper()
    try:
        url = f"https://jetapi.jtexpress.vn/track?billcode={code}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get('data') and len(res['data']) > 0:
            return res['data'][0].get('status', 'Đang xử lý')
        return "Không tìm thấy"
    except Exception as e:
        return "Lỗi API J&T"

# ================= SPX (VƯỢT TƯỜNG LỬA CHUẨN) =================
def check_spx(code):
    code = code.strip().upper() 
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Bắt buộc cho script chờ tối đa 15s để lấy dữ liệu
        driver.set_script_timeout(15)
        
        print(f"--- ĐANG MỞ CHROME KIỂM TRA: {code} ---")
        
        # BƯỚC 1: Vào trang chủ để lấy Cookie và vượt WAF
        driver.get("https://spx.vn/")
        time.sleep(3) # Đợi 3 giây cho nó nạp thẻ Session
        
        # BƯỚC 2: Gọi API ngầm ngay bên trong trình duyệt đã được tin tưởng
        js_script = f"""
        var callback = arguments[0];
        fetch('https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}')
            .then(response => response.json())
            .then(data => callback(data))
            .catch(err => callback({{"error": err.toString()}}));
        """
        
        # Thực thi Javascript và lấy kết quả trả về Python
        data = driver.execute_async_script(js_script)
        driver.quit() # Tắt Chrome ngay lập tức cho nhẹ máy
        
        print(f"Dữ liệu thu được: {str(data)[:300]}") # In ra log để phòng hờ
        
        if "error" in data:
            return "SPX chặn kết nối"

        if data.get("retcode") == 0 and data.get("data") and data["data"].get("tracking_list"):
            latest_tracking = data["data"]["tracking_list"][0]
            message = latest_tracking.get("message", "")
            message_lower = message.lower()

            if "giao hàng thành công" in message_lower or "đã được giao" in message_lower:
                return "✅ Đã giao"
            elif "đang giao hàng" in message_lower or "đang được giao" in message_lower:
                return "🚚 Đang giao"
            else:
                return f"🔄 {message}"
        else:
            return "Không tìm thấy/Chưa cập nhật"

    except Exception as e:
        print(f"SPX ERROR: {e}")
        return "SPX lỗi kết nối"

# ================= MAIN =================
def run():
    data = load_data()
    for code, info in data.items():
        if info.get("type") == "jnt":
            status = check_jnt(code)
        else:
            status = check_spx(code)

        if status != info.get("last"):
            data[code]["last"] = status
            save_data(data)
            send(f"📦 Mã vận đơn: <b>{code}</b>\n➡ Tình trạng: {status}")

if __name__ == "__main__":
    run()
