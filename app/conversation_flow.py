import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.models import IncomingMessage, Order
from app.database import get_session, save_session, reset_session, create_order, log_message
from app.whatsapp_client import whatsapp_client
from app.referral_parser import catalog, parse_incoming_referral
from app.ai_assistant import generate_ai_reply
from app.notifier import notify_new_order

logger = logging.getLogger("conversation_flow")

def handle_incoming_message(msg: IncomingMessage):
    """
    المنسق الرئيسي لمعالجة رسائل الزبائن وإدارة المحادثة والبيع
    """
    phone = msg.from_number
    text = (msg.text or "").strip()
    btn_id = msg.button_reply_id or msg.list_reply_id

    # تسجيل الرسالة الواردة
    log_message(phone, "incoming", text or f"[Button: {btn_id}]", source=msg.referral.source_type if msg.referral else "direct")

    # جلب الجلسة الحالية للعميل
    session = get_session(phone)
    state = session.get("state", "NEW")
    data = session.get("data", {})

    logger.info(f"Processing message from {phone} | State: {state} | Text: '{text}' | Button: '{btn_id}'")

    # 1. إذا كان زبوناً قادماً من إعلان جديد (ميتا أو تيك توك)
    if msg.referral and msg.referral.source_type in ["meta_ad", "tiktok_ad"]:
        matched_prod = catalog.get_by_id(msg.referral.matched_product_id) if msg.referral.matched_product_id else None
        
        # إذا لم يُحدد المنتج مسبقاً، نبحث عنه في الكتالوج
        if not matched_prod and msg.referral.headline:
            matched_prod = catalog.match_product(msg.referral.headline)

        if matched_prod:
            data["product_id"] = matched_prod.id
            data["product_name"] = matched_prod.name
            data["product_price"] = matched_prod.price_iqd
            data["source"] = msg.referral.source_type
            save_session(phone, "PRODUCT_OFFERED", data)

            welcome_text = (
                f"يا هلا ومية هلا بيك بـ {settings.STORE_NAME}! 🌸\n\n"
                f"شاهدت إعلان: *{matched_prod.name}*\n"
                f"• السعر: *{matched_prod.price_iqd:,} د.ع*\n"
                f"• {matched_prod.description}\n"
                f"• التوصيل متوفر لكافة محافظات العراق مع الدفع عند الاستلام 🚚\n\n"
                f"تحب نحجزلك قطعة هسة لو عندك أي استفسار عيوني؟"
            )
            buttons = [
                {"id": f"btn_order_{matched_prod.id}", "title": "🛒 اطلب الآن"},
                {"id": "btn_shipping", "title": "🚚 تفاصيل التوصيل"},
                {"id": "btn_store_url", "title": "🌐 زيارة المتجر"}
            ]
            whatsapp_client.send_interactive_buttons(phone, welcome_text, buttons)
            return

    # 2. معالجة ضغطات الأزرار (Button Replies)
    if btn_id:
        if btn_id.startswith("btn_order_"):
            prod_id = btn_id.replace("btn_order_", "")
            prod = catalog.get_by_id(prod_id)
            if prod:
                data["product_id"] = prod.id
                data["product_name"] = prod.name
                data["product_price"] = prod.price_iqd

            data["source"] = data.get("source", "button_order")
            save_session(phone, "AWAITING_NAME", data)

            msg_text = (
                "تدلل يا غالي، اختيارك ممتاز! 🌟\n"
                "حتى نثبت حجزك ونجهز الشحنة، تفضل اكتب لنا *(اسمك الكريم الثلاثي)* 👇"
            )
            whatsapp_client.send_text_message(phone, msg_text)
            return

        elif btn_id == "btn_shipping":
            shipping_info = (
                f"تفاصيل التوصيل في متجر زيزو 🚚:\n"
                f"• بغداد: {settings.SHIPPING_BAGHDAD:,} د.ع (خلال 24-48 ساعة)\n"
                f"• باقي المحافظات: {settings.SHIPPING_GOVERNORATES:,} د.ع (خلال 2-3 أيام)\n"
                f"• الدفع عند الاستلام مع حق فحص المنتج قبل الدفع ✅"
            )
            buttons = [
                {"id": f"btn_order_{data.get('product_id', 'prod_001')}", "title": "🛒 تأكيد الطلب"},
                {"id": "btn_store_url", "title": "🌐 رابط المتجر"}
            ]
            whatsapp_client.send_interactive_buttons(phone, shipping_info, buttons)
            return

        elif btn_id == "btn_store_url":
            store_msg = (
                f"تقدر تتصفح كافة منتجاتنا وعروضنا الحصرية بمتجر زيزو عبر الرابط التالي:\n"
                f"{settings.STORE_URL}\n\n"
                f"وإذا عجبك أي منتج هناك، تكدر تطلبه مباشرة من الموقع أو تراسلنا هنا وتدلل!"
            )
            whatsapp_client.send_text_message(phone, store_msg, preview_url=True)
            return

        elif btn_id == "btn_confirm_order":
            # إتمام الطلب وحفظه
            prod_name = data.get("product_name", "منتج من المتجر")
            prod_price = data.get("product_price", 25000)
            shipping = settings.SHIPPING_BAGHDAD if "بغداد" in str(data.get("address", "")) else settings.SHIPPING_GOVERNORATES
            total = prod_price + shipping

            new_order = Order(
                customer_phone=phone,
                customer_name=data.get("customer_name"),
                province=data.get("province", "العراق"),
                address=data.get("address"),
                product_id=data.get("product_id"),
                product_name=prod_name,
                product_price=prod_price,
                quantity=1,
                total_amount=total,
                source=data.get("source", "whatsapp_bot"),
                status="confirmed"
            )
            order_id = create_order(new_order)
            notify_new_order(new_order, order_id)
            reset_session(phone)

            success_msg = (
                f"🎉 ألف مبروك يا {new_order.customer_name or 'غالي'}، تم تثبيت طلبك بنجاح!\n\n"
                f"📌 *رقم الطلب:* #{order_id}\n"
                f"📦 *المنتج:* {prod_name}\n"
                f"💵 *المبلغ الإجمالي:* {total:,} د.ع (شامل التوصيل)\n"
                f"📍 *العنوان:* {new_order.address}\n\n"
                f"راح يتصل بيك مندوب التوصيل للتسليم قريباً.\n"
                f"شكراً لثقتك بـ {settings.STORE_NAME} 🌸"
            )
            whatsapp_client.send_text_message(phone, success_msg)
            return

        elif btn_id == "btn_cancel_order":
            reset_session(phone)
            cancel_msg = "تم إلغاء الطلب عيوني. بأي وقت تحتاج أي شي إحنا بالخدمة دائماً! 🌹"
            whatsapp_client.send_text_message(phone, cancel_msg)
            return

    # 3. معالجة مراحل جمع البيانات (Form Steps)
    if state == "AWAITING_NAME":
        data["customer_name"] = text
        save_session(phone, "AWAITING_ADDRESS", data)
        reply = (
            f"عاشت الأسامي يا {text} 🌹\n"
            f"هسة تفضل دز لنا *(المحافظة والمنطقة وأقرب نقطة دالة)*:"
        )
        whatsapp_client.send_text_message(phone, reply)
        return

    elif state == "AWAITING_ADDRESS":
        data["address"] = text
        save_session(phone, "CONFIRMING_ORDER", data)

        prod_name = data.get("product_name", "المنتج المختار")
        prod_price = data.get("product_price", 25000)
        shipping = settings.SHIPPING_BAGHDAD if "بغداد" in text else settings.SHIPPING_GOVERNORATES
        total = prod_price + shipping

        summary_text = (
            f"يرجى مراجعة تفاصيل طلبك لتأكيده عيوني 📋:\n\n"
            f"👤 *الاسم:* {data.get('customer_name')}\n"
            f"📱 *رقم الهاتف:* {phone}\n"
            f"📍 *العنوان:* {text}\n"
            f"🛍️ *المنتج:* {prod_name}\n"
            f"💰 *سعر المنتج:* {prod_price:,} د.ع\n"
            f"🚚 *أجور التوصيل:* {shipping:,} د.ع\n"
            f"💵 *المجموع الكلي عند الاستلام:* *{total:,} د.ع*\n\n"
            f"اضغط على تأكيد للبدء بالتجهيز 👇"
        )
        buttons = [
            {"id": "btn_confirm_order", "title": "✅ تأكيد الطلب"},
            {"id": "btn_cancel_order", "title": "❌ إلغاء"}
        ]
        whatsapp_client.send_interactive_buttons(phone, summary_text, buttons)
        return

    # 4. إذا ذكر الزبون منتجاً بالاسم في رسالته العادية
    matched_prod = catalog.match_product(text)
    if matched_prod and state in ["NEW", "PRODUCT_OFFERED"]:
        data["product_id"] = matched_prod.id
        data["product_name"] = matched_prod.name
        data["product_price"] = matched_prod.price_iqd
        save_session(phone, "PRODUCT_OFFERED", data)

        prod_text = (
            f"يا هلا بيك! بخصوص *{matched_prod.name}* 🌟\n"
            f"• السعر: *{matched_prod.price_iqd:,} د.ع*\n"
            f"• {matched_prod.description}\n"
            f"• التوصيل لكافة محافظات العراق والدفع عند الاستلام.\n\n"
            f"تحب نثبتلك حجز قطعة؟"
        )
        buttons = [
            {"id": f"btn_order_{matched_prod.id}", "title": "🛒 اطلب الآن"},
            {"id": "btn_shipping", "title": "🚚 تفاصيل التوصيل"}
        ]
        whatsapp_client.send_interactive_buttons(phone, prod_text, buttons)
        return

    # 5. في أي وقت آخر: الذكاء الاصطناعي يجيب بلباقة ويقترح الخطوة المناسبة
    ai_reply = generate_ai_reply(text, session_context=data)
    whatsapp_client.send_text_message(phone, ai_reply)
