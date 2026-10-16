import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.referral_parser import catalog, parse_incoming_referral
from app.database import init_db, get_session, reset_session, get_all_orders
from app.conversation_flow import handle_incoming_message
from app.models import IncomingMessage, ReferralData

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == "متجر زيزو"
    assert data["status"] == "online"

def test_webhook_verification():
    # اختبار الـ Verify Token الصحيح
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.VERIFY_TOKEN,
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 200
    assert response.text == "1158201444"

    # اختبار التوكن الخاطئ
    response_fail = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1158201444"
        }
    )
    assert response_fail.status_code == 403

def test_catalog_matching():
    # مطابقة عبر الكلمات المفتاحية
    p1 = catalog.match_product("اريد اشتري مفرمة لحم")
    assert p1 is not None
    assert p1.id == "prod_001"

    # مطابقة عبر كود تيك توك
    p2 = catalog.match_product("اعلان تيك توك chopper2l")
    assert p2 is not None
    assert p2.id == "prod_001"

    # مطابقة عبر اسم المنتج
    p3 = catalog.match_product("مكواة بخار عمودية")
    assert p3 is not None
    assert p3.id == "prod_002"

def test_referral_parsing_meta():
    raw_meta_msg = {
        "from": "9647712345678",
        "id": "wamid_1",
        "type": "text",
        "text": {"body": "مرحبا"},
        "referral": {
            "source_type": "ad",
            "source_id": "meta_ad_999",
            "headline": "مفرمة وخلاط كهربائي 2 لتر",
            "body": "عروض متجر زيزو"
        }
    }
    ref_data, prod = parse_incoming_referral(raw_meta_msg)
    assert ref_data.source_type == "meta_ad"
    assert prod is not None
    assert prod.id == "prod_001"

def test_referral_parsing_tiktok():
    raw_tiktok_msg = {
        "from": "9647712345678",
        "id": "wamid_2",
        "type": "text",
        "text": {"body": "مرحبا شفت الاعلان على تيك توك كود chopper2l"}
    }
    ref_data, prod = parse_incoming_referral(raw_tiktok_msg)
    assert ref_data.source_type == "tiktok_ad"
    assert prod is not None
    assert prod.id == "prod_001"

def test_full_sales_funnel():
    test_phone = "964779998877"
    reset_session(test_phone)

    # 1. رسالة إعلان ميتا
    msg1 = IncomingMessage(
        from_number=test_phone,
        message_id="msg_1",
        timestamp="1000",
        text="مرحبا",
        referral=ReferralData(
            source_type="meta_ad",
            headline="مفرمة وخلاط كهربائي",
            matched_product_id="prod_001"
        )
    )
    handle_incoming_message(msg1)
    session = get_session(test_phone)
    assert session["state"] == "PRODUCT_OFFERED"
    assert session["data"]["product_id"] == "prod_001"

    # 2. الزبون يضغط على زر الطلب
    msg2 = IncomingMessage(
        from_number=test_phone,
        message_id="msg_2",
        timestamp="1001",
        button_reply_id="btn_order_prod_001"
    )
    handle_incoming_message(msg2)
    session = get_session(test_phone)
    assert session["state"] == "AWAITING_NAME"

    # 3. الزبون يرسل اسمه
    msg3 = IncomingMessage(
        from_number=test_phone,
        message_id="msg_3",
        timestamp="1002",
        text="علي كاظم العراقي"
    )
    handle_incoming_message(msg3)
    session = get_session(test_phone)
    assert session["state"] == "AWAITING_ADDRESS"
    assert session["data"]["customer_name"] == "علي كاظم العراقي"

    # 4. الزبون يرسل عنوانه في بغداد
    msg4 = IncomingMessage(
        from_number=test_phone,
        message_id="msg_4",
        timestamp="1003",
        text="بغداد - المنصور - شارع 14 رمضان قرب مول المنصور"
    )
    handle_incoming_message(msg4)
    session = get_session(test_phone)
    assert session["state"] == "CONFIRMING_ORDER"
    assert "بغداد" in session["data"]["address"]

    # 5. الزبون يؤكد الطلب
    msg5 = IncomingMessage(
        from_number=test_phone,
        message_id="msg_5",
        timestamp="1004",
        button_reply_id="btn_confirm_order"
    )
    handle_incoming_message(msg5)

    # الجلسة يعاد تعيينها بعد نجاح الطلب
    session_after = get_session(test_phone)
    assert session_after["state"] == "NEW"

    # التأكد من تسجيل الطلب في قاعدة البيانات
    orders = get_all_orders()
    matching_orders = [o for o in orders if o["customer_phone"] == test_phone]
    assert len(matching_orders) >= 1
    latest_order = matching_orders[0]
    assert latest_order["customer_name"] == "علي كاظم العراقي"
    assert latest_order["product_id"] == "prod_001"
    # سعر المنتج (25000) + توصيل بغداد (5000) = 30000 د.ع
    assert latest_order["total_amount"] == 30000
    assert latest_order["status"] == "confirmed"

def test_orders_api_and_export():
    # فحص API الطلبات
    resp = client.get("/api/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data

    # فحص تصدير CSV
    export_resp = client.get("/api/orders/export")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/csv")
    assert "Customer Phone" in export_resp.text
