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

        url = "https://spx.vn/api/v2/fleet_order/tracking/search"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "tracking_number": code
        }

        res = requests.post(url, json=payload, headers=headers, timeout=10)

        data = res.json()

        # debug
        print(data)

        if "data" in data and data["data"]:
            status = data["data"][0]["status"]
            return status
        else:
            return "Không tìm thấy"

    except Exception as e:
        print(e)
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
    
