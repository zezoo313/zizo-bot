import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings
from app.models import ReferralData, Product

logger = logging.getLogger("referral_parser")

class ProductCatalog:
    def __init__(self):
        self.products: List[Product] = []
        self.load_catalog()

    def load_catalog(self):
        try:
            with open(settings.CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.products = [Product(**p) for p in data]
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            self.products = []

    def get_by_id(self, product_id: str) -> Optional[Product]:
        for p in self.products:
            if p.id == product_id:
                return p
        return None

    def match_product(self, text: str) -> Optional[Product]:
        """البحث عن منتج يطابق النص عبر الكلمات المفتاحية أو الكود"""
        if not text:
            return None
        text_lower = text.lower()

        # 1. فحص كود تيك توك المباشر
        for p in self.products:
            if p.tiktok_code and p.tiktok_code.lower() in text_lower:
                return p

        # 2. فحص اسم المنتج المباشر
        for p in self.products:
            if p.name.lower() in text_lower:
                return p

        # 3. فحص الكلمات المفتاحية
        for p in self.products:
            for kw in p.keywords:
                if kw.lower() in text_lower:
                    return p

        return None

catalog = ProductCatalog()

def parse_incoming_referral(raw_message: Dict[str, Any]) -> Tuple[ReferralData, Optional[Product]]:
    """
    تحليل الرسالة لمعرفة هل العميل قادم من إعلان ميتا أو تيك توك وتحديد المنتج
    """
    referral_obj = raw_message.get("referral")
    text_body = ""
    if raw_message.get("type") == "text":
        text_body = raw_message.get("text", {}).get("body", "")

    # 1. إذا كان قادماً من إعلان ميتا (Click-to-WhatsApp)
    if referral_obj:
        headline = referral_obj.get("headline", "")
        body = referral_obj.get("body", "")
        source_id = referral_obj.get("source_id", "")
        source_type = referral_obj.get("source_type", "ad")
        image_url = referral_obj.get("image_url")
        video_url = referral_obj.get("video_url")

        # محاولة مطابقة المنتج من عنوان إعلان ميتا
        matched_prod = catalog.match_product(headline) or catalog.match_product(body) or catalog.match_product(text_body)

        ref_data = ReferralData(
            source_type="meta_ad",
            source_id=source_id,
            headline=headline,
            body=body,
            image_url=image_url,
            video_url=video_url,
            matched_product_id=matched_prod.id if matched_prod else None
        )
        return ref_data, matched_prod

    # 2. إذا كان قادماً من إعلان تيك توك (عبر رابط wa.me بنص ترويجي)
    tiktok_triggers = ["تيك توك", "تيكتوك", "tiktok", "tt_"]
    is_tiktok = any(trigger in text_body.lower() for trigger in tiktok_triggers)

    if is_tiktok:
        matched_prod = catalog.match_product(text_body)
        ref_data = ReferralData(
            source_type="tiktok_ad",
            source_id="tiktok_campaign",
            headline="إعلان تيك توك",
            body=text_body,
            matched_product_id=matched_prod.id if matched_prod else None
        )
        return ref_data, matched_prod

    # 3. زائر عادي أو استفسار عام
    matched_prod = catalog.match_product(text_body)
    ref_data = ReferralData(
        source_type="organic",
        matched_product_id=matched_prod.id if matched_prod else None
    )
    return ref_data, matched_prod
