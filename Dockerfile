# 使用官方 Python 3.11 slim 映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有應用程式檔案
COPY . .

# 設定環境變數 - Cloud Run Jobs 專用
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 建立非 root 使用者
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 執行 main.py
CMD ["python", "main.py"]