FROM python:3.12-slim

WORKDIR /app

# نسخ وتثبيت الحزم
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# المنفذ
ENV PORT=8000
EXPOSE 8000

# أمر التشغيل
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
