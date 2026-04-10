import requests
import json

TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

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
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        import time

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        driver.get("https://spx.vn/")
        time.sleep(5)

        input_box = driver.find_element(By.XPATH, "//input")
        input_box.send_keys(code)

        time.sleep(5)

        status = driver.page_source

        driver.quit()

        if "Đang giao" in status:
            return "Đang giao"
        elif "Đã giao" in status:
            return "Đã giao"
        else:
            return "Đang xử lý"

    except:
        return "Lỗi SPX"

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
    