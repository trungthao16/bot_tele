import requests
import json
# Import thêm các vũ khí hạng nặng (Selenium) đã có sẵn trong máy chủ của bạn
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

# ================= SPX (DÙNG TRÌNH DUYỆT ẨN) =================
def check_spx(code):
    code = code.strip().upper() 
    try:
        # Cấu hình mở Chrome ẩn không hiện giao diện
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        print(f"--- ĐANG MỞ CHROME KIỂM TRA: {code} ---")
        
        # Khởi động Chrome
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Truy cập thẳng vào hệ thống API của Shopee bằng Chrome
        url = f"https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}"
        driver.get(url)
        
        # Rút ruột dữ liệu JSON trả về trên màn hình
        content = driver.find_element("tag name", "body").text
        driver.quit() # Tắt Chrome cho nhẹ máy
        
        print(f"Response: {content[:300]}") # In ra log để dự phòng
        
        data = json.loads(content)
        
        if data.get("retcode") == 0 and data.get("data") and data["data"].get("tracking_list"):
            latest_tracking = data["data"]["tracking_list"][0]
            message = latest_tracking.get("message", "")
            message_lower = message.lower()

            # Dò đúng từ khóa
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
