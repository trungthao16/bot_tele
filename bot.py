import requests
import json

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

# ================= SPX =================
def check_spx(code):
    # Dọn dẹp mã vận đơn (xóa khoảng trắng thừa và viết hoa)
    code = code.strip().upper() 
    
    try:
        url = f"https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}"
        
        # Bổ sung bộ Header siêu giống trình duyệt thật để vượt mặt tường lửa
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://spx.vn/",
            "Origin": "https://spx.vn",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        res = requests.get(url, headers=headers, timeout=15)
        
        # --- PHẦN DEBUG QUAN TRỌNG ĐỂ XEM LỖI ---
        print(f"--- ĐANG KIỂM TRA MÃ: {code} ---")
        print(f"Status Code: {res.status_code}")
        print(f"Response Text: {res.text[:300]}") # In ra 300 ký tự trả về
        # ----------------------------------------
        
        if res.status_code != 200:
            return f"SPX lỗi ({res.status_code})"
            
        data = res.json()
        
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
