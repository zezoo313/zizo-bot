import sys
import time
import requests
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def print_separator(title):
    print("\n" + "=" * 60)
    print(f"🔹 {title}")
    print("=" * 60)

def simulate():
    print_separator("فحص الخادم الحي لمتجر زيزو")
    res = requests.get(f"{BASE_URL}/")
    print("استجابة الخادم الرئيسية:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))

    # محاكاة زبون قادم من إعلان ميتا (فيسبوك)
    customer_phone = "9647712345678"
    print_separator("1. محاكاة زبون قادم من إعلان ميتا (Click-to-WhatsApp)")
    payload_meta = {
        "phone": customer_phone,
        "text": "مرحباً، شفت الإعلان وأريد أعرف تفاصيل",
        "referral": {
            "source_type": "ad",
            "source_id": "meta_campaign_101",
            "headline": "مفرمة وخلاط كهربائي متعدد الاستخدامات 2 لتر",
            "body": "خصم خاص على مفرمة اللحم والخضار"
        }
    }
    r = requests.post(f"{BASE_URL}/api/simulate-message", json=payload_meta)
    print("تم إرسال الحدث إلى البوت، الحالة:", r.status_code)
    time.sleep(0.5)

    # الزبون يضغط على زر الطلب
    print_separator("2. الزبون يضغط زر [🛒 اطلب الآن]")
    payload_order_btn = {
        "phone": customer_phone,
        "button_id": "btn_order_prod_001"
    }
    requests.post(f"{BASE_URL}/api/simulate-message", json=payload_order_btn)
    time.sleep(0.5)

    # الزبون يرسل اسمه
    print_separator("3. الزبون يرسل اسمه: سجاد أحمد التميمي")
    payload_name = {
        "phone": customer_phone,
        "text": "سجاد أحمد التميمي"
    }
    requests.post(f"{BASE_URL}/api/simulate-message", json=payload_name)
    time.sleep(0.5)

    # الزبون يرسل عنوانه في بغداد
    print_separator("4. الزبون يرسل عنوانه: بغداد - حي الجامعة - شارع الربيع")
    payload_address = {
        "phone": customer_phone,
        "text": "بغداد - حي الجامعة - شارع الربيع قرب جامع الملا حويش"
    }
    requests.post(f"{BASE_URL}/api/simulate-message", json=payload_address)
    time.sleep(0.5)

    # الزبون يؤكد الطلب بالضغط على [✅ تأكيد الطلب]
    print_separator("5. الزبون يضغط زر [✅ تأكيد الطلب]")
    payload_confirm = {
        "phone": customer_phone,
        "button_id": "btn_confirm_order"
    }
    requests.post(f"{BASE_URL}/api/simulate-message", json=payload_confirm)
    time.sleep(0.5)

    # محاكاة زبون قادم من تيك توك
    print_separator("6. محاكاة زبون آخر قادم من إعلان تيك توك")
    tiktok_phone = "9647801122334"
    payload_tiktok = {
        "phone": tiktok_phone,
        "text": "مرحبا اريد طلب المنتج من اعلان تيكتوك كود steamer"
    }
    requests.post(f"{BASE_URL}/api/simulate-message", json=payload_tiktok)
    time.sleep(0.5)

    # استعراض الطلبات المسجلة في النظام
    print_separator("7. استعلام عن الطلبات المسجلة في قاعدة البيانات (/api/orders)")
    orders_res = requests.get(f"{BASE_URL}/api/orders")
    orders = orders_res.json().get("orders", [])
    print(f"إجمالي الطلبات المسجلة: {len(orders)}")
    for o in orders[:3]:
        print(f"- طلب #{o['id']}: الزبون '{o['customer_name']}' | هاتف: {o['customer_phone']} | منتج: {o['product_name']} | المبلغ: {o['total_amount']:,} د.ع | المصدر: {o['source']}")

if __name__ == "__main__":
    simulate()
