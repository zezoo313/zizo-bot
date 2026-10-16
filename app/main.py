import logging
import io
import csv
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Query, Response, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from app.config import settings
from app.database import init_db, get_all_orders
from app.models import IncomingMessage
from app.referral_parser import parse_incoming_referral
from app.conversation_flow import handle_incoming_message

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s")
logger = logging.getLogger("zizo_bot_main")

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

app = FastAPI(
    title="Zizo Store WhatsApp Auto-Reply Bot",
    description="بوت مخصص للرد الآلي على إعلانات ميتا وتيك توك عبر واتساب لمتجر زيزو",
    version="1.0.0"
)

@app.get("/")
def home():
    orders = get_all_orders()
    return {
        "status": "online",
        "store_name": settings.STORE_NAME,
        "store_url": settings.STORE_URL,
        "phone": settings.STORE_PHONE,
        "meta_page_id": settings.META_PAGE_ID,
        "orders_count": len(orders),
        "docs": "/docs"
    }

@app.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    التحقق الأمني من الـ Webhook الخاص بشركة Meta (Facebook/WhatsApp)
    """
    logger.info(f"Received webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("Webhook successfully verified by Meta!")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.warning("Webhook verification failed: Invalid verify token.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    استقبال الرسائل وأحداث الـ Webhook من WhatsApp Cloud API
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # فحص بنية رسائل ميتا القياسية
    entry_list = body.get("entry", [])
    if not entry_list:
        return {"status": "ignored_no_entry"}

    for entry in entry_list:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                from_num = msg.get("from")
                msg_id = msg.get("id")
                timestamp = msg.get("timestamp", "")
                msg_type = msg.get("type")

                text_content = None
                button_reply_id = None
                list_reply_id = None

                if msg_type == "text":
                    text_content = msg.get("text", {}).get("body")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    i_type = interactive.get("type")
                    if i_type == "button_reply":
                        button_reply_id = interactive.get("button_reply", {}).get("id")
                    elif i_type == "list_reply":
                        list_reply_id = interactive.get("list_reply", {}).get("id")

                # تحليل الإحالة إن وجدت (ميتا أو تيك توك)
                referral_data, matched_prod = parse_incoming_referral(msg)

                incoming = IncomingMessage(
                    from_number=from_num,
                    message_id=msg_id,
                    timestamp=timestamp,
                    text=text_content,
                    button_reply_id=button_reply_id,
                    list_reply_id=list_reply_id,
                    referral=referral_data
                )

                # معالجة الرسالة في الخلفية لضمان الاستجابة السريعة لميتا بـ 200 OK
                background_tasks.add_task(handle_incoming_message, incoming)

    return {"status": "success"}

@app.get("/api/orders")
def list_orders():
    """عرض جميع الطلبات المستلمة"""
    return {"orders": get_all_orders()}

@app.get("/api/orders/export")
def export_orders_csv():
    """تصدير سجل الطلبات كملف Excel / CSV"""
    orders = get_all_orders()
    output = io.StringIO()
    writer = csv.writer(output)

    # رأس الجدول
    writer.writerow(["ID", "Customer Phone", "Customer Name", "Province", "Address", "Product", "Price IQD", "Quantity", "Total IQD", "Source", "Status", "Date"])

    for o in orders:
        writer.writerow([
            o.get("id"),
            o.get("customer_phone"),
            o.get("customer_name"),
            o.get("province"),
            o.get("address"),
            o.get("product_name"),
            o.get("product_price"),
            o.get("quantity"),
            o.get("total_amount"),
            o.get("source"),
            o.get("status"),
            o.get("created_at")
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=zizo_orders.csv"}
    )

@app.post("/api/simulate-message")
def simulate_message(payload: Dict[str, Any]):
    """
    نقطة اختبار لمحاكاة رسائل الزبائن أو الإعلانات بدون الحاجة لواتساب حقيقي
    مثال:
    {"phone": "9647700000000", "text": "مرحبا شفت الاعلان على تيك توك واريد مفرمة"}
    """
    phone = payload.get("phone", "9647700000000")
    text = payload.get("text", "")
    button_id = payload.get("button_id")
    referral_obj = payload.get("referral")

    raw_msg: Dict[str, Any] = {
        "from": phone,
        "id": "sim_123",
        "type": "text" if text else "interactive",
        "text": {"body": text} if text else {},
        "referral": referral_obj
    }
    ref_data, prod = parse_incoming_referral(raw_msg)

    incoming = IncomingMessage(
        from_number=phone,
        message_id="sim_msg_001",
        timestamp="12345678",
        text=text,
        button_reply_id=button_id,
        referral=ref_data
    )
    handle_incoming_message(incoming)
    return {"status": "processed", "simulated_message": incoming}
