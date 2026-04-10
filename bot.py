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
    # Dùng parse_mode HTML để làm đậm mã đơn hàng cho đẹp
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

# ================= J&T =================
def check_jnt(code):
    try:
        url = f"https://jetapi.jtexpress.vn/track?billcode={code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get('data') and len(res['data']) > 0:
            return res['data'][0].get('status', 'Đang xử lý')
        return "Không tìm thấy"
    except Exception as e:
        print(f"J&T ERROR: {e}")
        return "Lỗi API J&T"

# ================= SPX =================
def check_spx(code):
    try:
        # Sử dụng API trực tiếp từ trang chủ SPX VN
        url = f"https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://spx.vn/"
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            return f"SPX lỗi ({res.status_code})"
            
        data = res.json()
        
        # Kiểm tra xem có dữ liệu hành trình không
        if data.get("retcode") == 0 and data.get("data") and data["data"].get("tracking_list"):
            # Lấy mốc thời gian mới nhất (thường nằm ở index 0)
            latest_tracking = data["data"]["tracking_list"][0]
            message = latest_tracking.get("message", "")
            message_lower = message.lower()

            # Dựa vào hình ảnh bạn cung cấp để map trạng thái
            if "giao hàng thành công" in message_lower or "đã được giao" in message_lower:
                return "✅ Đã giao"
            elif "đang giao hàng" in message_lower or "đang được giao bởi dịch vụ" in message_lower:
                return "🚚 Đang giao"
            else:
                # Nếu đang luân chuyển, trả về nội dung mới nhất (VD: "Đang dỡ hàng tại...")
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

        # Chỉ thông báo khi trạng thái thay đổi
        if status != info.get("last"):
            data[code]["last"] = status
            save_data(data)
            
            # Nếu đã giao thành công thì có thể cân nhắc xóa luôn khỏi file data để đỡ request
            send(f"📦 Mã vận đơn: <b>{code}</b>\n➡ Tình trạng: {status}")

if __name__ == "__main__":
    run()
