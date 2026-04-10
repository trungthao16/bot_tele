# Sử dụng hệ điều hành Debian siêu nhẹ được cài sẵn Python
FROM python:3.10-slim

# Cài đặt trình duyệt Chromium chuẩn không bị lỗi Snap
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục làm việc cho Bot
WORKDIR /app

# Khai báo và cài đặt các thư viện Python (requests, selenium...)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code bot.py và data.json của bạn vào máy chủ
COPY . .

# Lệnh cuối cùng để khởi động Bot
CMD ["python", "bot.py"]
