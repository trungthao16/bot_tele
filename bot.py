import requests
import json

TOKEN = "8597164941:AAFooj7wISO14SoP7wTROfAt8kMhcICa6ns"
CHAT_ID = "5444530262"

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ================= J&T =================
def check_jnt(code):
    try:
        url = f"https://jetapi.jtexpress.vn/track?billcode={code}"
        res = requests.get(url, timeout=10).json()
        return res['data']['status']
    except:
        return "Lỗi J&T"

# ================= SPX =================
def check_spx(code):
    try:
        import requests
        from bs4 import BeautifulSoup

        url = f"https://parcelsapp.com/en/tracking/{code}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return "SPX lỗi"

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text().lower()

        # debug (in log GitHub)
        print(text[:500])

        if "delivered" in text:
            return "Đã giao"
        elif "in transit" in text or "out for delivery" in text:
            return "Đang giao"
        elif "not found" in text:
            return "Không tìm thấy"
        else:
            return "Đang xử lý"

    except Exception as e:
        print("SPX ERROR:", e)
        return "SPX lỗi"

# ================= MAIN =================
def run():
    data = load_data()

    for code, info in data.items():
        if info["type"] == "jnt":
            status = check_jnt(code)
        else:
            status = check_spx(code)

        if status != info["last"]:
            data[code]["last"] = status
            save_data(data)
            send(f"📦 {code}\n➡ {status}")

if __name__ == "__main__":
    run()


    # tạo cron job để chạy script mỗi 10 phút
    
