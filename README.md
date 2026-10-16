# 🤖 نظام بوت واتساب متجر زيزو (Zizo Store WhatsApp Bot)

نظام رد وتفاعل آلي مخصص لاستقبال وتوجيه الزبائن القادمين من إعلانات **ميتا (Facebook / Instagram)** وإعلانات **تيك توك (TikTok)** إلى واتساب متجر زيزو (`+9647765496038`) وربطها بمتجر `https://rolemall.com/pYCsO5oshop`.

---

## 🌟 الميزات الرئيسية

1. **التعرف التلقائي على إعلانات ميتا (Click-to-WhatsApp):**
   - يلتقط البوت كائن `referral` المرسل من ميتا، ويعرف المنتج فوراً من عنوان الإعلان.
2. **التعرف التلقائي على إعلانات تيك توك:**
   - من خلال روابط `wa.me` المجهزة مسبقاً، يتعرف البوت على المنتج المطلوب.
3. **مساعد مبيعات ذكي باللهجة العراقية:**
   - يرحب بالزبون ("يا هلا بيك"، "تدلل عيوني").
   - يشرح مواصفات المنتج والأسعار بالدينار العراقي (IQD).
   - يوضح تفاصيل التوصيل (بغداد 5,000 د.ع، المحافظات 6,000 د.ع).
4. **تجميع وتأكيد الطلبات تلقائياً:**
   - يجمع الاسم، المحافظة، وأقرب نقطة دالة، ويحسب المجموع الكلي مع التوصيل.
   - يثبت الطلب في قاعدة بيانات محلية (SQLite).
   - يرسل إشعاراً فورياً للبريد `dandana600@gmail.com`.
   - يتيح تصدير الطلبات كملف Excel / CSV بنقرة واحدة.

---

## 🚀 التثبيت والتشغيل المحلي

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. إعداد ملف البيئة
انسخ ملف `.env.example` إلى `.env`:
```bash
cp .env.example .env
```

### 3. تشغيل الخادم
```bash
uvicorn app.main:app --reload --port 8000
```
سيكون الخادم متاحاً على: `http://localhost:8000`  
وواجهة التوثيق التفاعلية (Swagger API): `http://localhost:8000/docs`

---

## 🔗 خطوات الربط مع Meta for Developers

1. ادخل إلى **[Meta for Developers](https://developers.facebook.com/)** وسجل الدخول بحسابك المرتبط بصفحتك (`113475771676357`).
2. اضغط على **My Apps** ثم **Create App** واختر النوع **Business**.
3. أضف منتج **WhatsApp** إلى التطبيق.
4. من القائمة الجانبية: **WhatsApp > Configuration**:
   - ضع رابط الـ Webhook الخاص بسيرفرك (مثال: `https://your-domain.com/webhook` أو عبر رابط Ngrok أثناء التجربة).
   - ضع رمز التحقق (Verify Token):
     `zizo_secret_verify_token_2026`
   - اضغط **Verify and Save**.
   - في خانة Webhook fields، اضغط **Manage** وفعل خيار **`messages`**.
5. اربط رقم هاتفك `07765496038` عبر **WhatsApp > API Setup** وانسخ:
   - `Temporary Access Token` أو `Permanent Token` إلى `WHATSAPP_TOKEN` في `.env`.
   - `Phone Number ID` إلى `PHONE_NUMBER_ID` في `.env`.

---

## 📱 توليد روابط إعلانات تيك توك (TikTok Ads Links)

في إعلانات تيك توك، ضع الرابط التالي في زر الإعلان (CTA):
```text
https://wa.me/9647765496038?text=مرحبا_اريد_طلب_المنتج_من_اعلان_تيكتوك_كود_chopper2l
```
> يمكنك استبدال `chopper2l` بأي كود منتج موجود في `data/products_catalog.json`.

---

## 🧪 فحص واختبار النظام

لتشغيل الاختبارات التلقائية والتأكد من سلامة الكود ومسار المحادثة بالكامل:
```bash
pytest tests/test_bot.py -v
```

---

## 📊 إدارة وتصدير الطلبات

- **عرض الطلبات:** افتح `http://localhost:8000/api/orders`
- **تحميل ملف إكسل CSV بالطلبات:** افتح `http://localhost:8000/api/orders/export`
- **رابط المتجر الأساسي:** [متجر زيزو على Rolemall](https://rolemall.com/pYCsO5oshop)
