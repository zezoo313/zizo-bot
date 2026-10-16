import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # إعدادات متجر زيزو
    STORE_NAME: str = "متجر زيزو"
    STORE_URL: str = "https://rolemall.com/pYCsO5oshop"
    STORE_PHONE: str = "07765496038"
    STORE_PHONE_INTL: str = "9647765496038"
    META_PAGE_ID: str = "113475771676357"
    NOTIFICATION_EMAIL: str = "dandana600@gmail.com"

    # تكلفة التوصيل في العراق (بالدينار العراقي)
    SHIPPING_BAGHDAD: int = 5000
    SHIPPING_GOVERNORATES: int = 6000

    # إعدادات WhatsApp Cloud API الرسمية
    WHATSAPP_TOKEN: str = "EAAG..."
    PHONE_NUMBER_ID: str = "1234567890"
    VERIFY_TOKEN: str = "zizo_secret_verify_token_2026"
    META_API_VERSION: str = "v21.0"

    # الذكاء الاصطناعي (اختياري، يعمل النظام بقواعد ذكية إن لم يتوفر المفتاح)
    GEMINI_API_KEY: str = ""

    # مسار قاعدة البيانات والكتالوج
    DATABASE_PATH: str = str(BASE_DIR / "data" / "zizo_store.db")
    CATALOG_PATH: str = str(BASE_DIR / "data" / "products_catalog.json")

    # إعدادات البريد SMTP (اختياري لإرسال إشعارات الإيميل)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
