import logging
import requests
from typing import Optional, Dict, Any
from app.config import settings
from app.referral_parser import catalog

logger = logging.getLogger("ai_assistant")

SYSTEM_PROMPT = f"""
أنت مساعد مبيعات ذكي وودود جداً تعمل لصالح "{settings.STORE_NAME}" في العراق.
تتحدث باللهجة العراقية اللطيفة والمحترمة (تستخدم كلمات مثل: "تدلل عيوني"، "يا هلا بيك"، "كل الهلا"، "تأمر أمر").
المعلومات الأساسية عن المتجر:
- اسم المتجر: {settings.STORE_NAME}
- رابط المتجر الإلكتروني: {settings.STORE_URL}
- خدمة التوصيل متوفرة لجميع محافظات العراق (بغداد: {settings.SHIPPING_BAGHDAD:,} د.ع، باقي المحافظات: {settings.SHIPPING_GOVERNORATES:,} د.ع).
- مدة التوصيل: بغداد خلال 24-48 ساعة، باقي المحافظات خلال 2-3 أيام.
- طريقة الدفع: الدفع عند الاستلام مع إمكانية فحص المنتج قبل الاستلام.

وظيفتك:
1. الإجابة بلباقة واختصار على أسئلة الزبائن بخصوص المنتجات، الأسعار، والتوصيل.
2. تشجيع الزبون على تأكيد طلبه الآن أو إعطائه رابط المتجر للتسوق.
3. تجنب الردود الطويلة جداً، واجعل المحادثة مشوقة ومريحة للمشتري.
"""

def generate_ai_reply(user_message: str, session_context: Optional[Dict[str, Any]] = None) -> str:
    """
    توليد رد ذكي باللهجة العراقية إما عبر Gemini API أو عبر القواعد الذكية المحلية
    """
    # 1. إذا كان مفتاح Gemini متوفراً
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"{SYSTEM_PROMPT}\n\nرسالة الزبون: {user_message}\nرد المساعد:"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250}
            }
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return reply
        except Exception as e:
            logger.error(f"Gemini API error: {e}")

    # 2. نظام الردود الذكية المحلي في حال عدم تفعيل مفتاح AI
    text = user_message.lower().strip()

    if any(w in text for w in ["توصيل", "شحن", "محافظات", "بغداد"]):
        return (
            f"التوصيل متوفر لكل محافظات العراق عيوني 🚚\n"
            f"• بغداد: {settings.SHIPPING_BAGHDAD:,} دينار (يوصلك خلال 24-48 ساعة)\n"
            f"• باقي المحافظات: {settings.SHIPPING_GOVERNORATES:,} دينار (يوصلك خلال يومين إلى ثلاثة)\n"
            f"والدفع عند الاستلام بعد ما تعاين طلبك."
        )

    if any(w in text for w in ["دفع", "فلوس", "زين كاش", "ماستر"]):
        return (
            "طريقة الدفع عندنا سهلة وآمنة: (الدفع عند الاستلام) بعد ما يوصلك المندوب وتفحص المنتج براحتك 📦✨"
        )

    if any(w in text for w in ["موقع", "رابط", "متجر", "باقي المنتجات", "الكتالوج"]):
        return (
            f"تقدر تتصفح كل منتجاتنا وعروضنا الحصرية بمتجر زيزو من هذا الرابط المباشر:\n{settings.STORE_URL}"
        )

    if any(w in text for w in ["شكرا", "تسلم", "مشكور", "ممنون"]):
        return "تدلل يا غالي بأي وقت، وإحنا بالخدمة دائماً! 🌸"

    # التحقق إن كان يسأل عن منتج معين
    matched_prod = catalog.match_product(text)
    if matched_prod:
        return (
            f"يا هلا بيك! بخصوص {matched_prod.name} 🌟\n"
            f"• السعر: {matched_prod.price_iqd:,} دينار عراقي.\n"
            f"• المواصفات: {matched_prod.description}\n\n"
            f"تحب نحجزلك قطعة منها هسة؟"
        )

    return (
        f"يا هلا ومية هلا بيك بـ {settings.STORE_NAME} 🌸\n"
        f"تدلل عيوني، كول لي شنو المنتج اللي عجبك حتى أفيدك بتفاصيله وسعره؟\n"
        f"أو تكدر تتصفح المتجر مباشرة عبر الرابط:\n{settings.STORE_URL}"
    )
