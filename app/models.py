from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Product(BaseModel):
    id: str
    name: str
    category: str
    price_iqd: int
    description: str
    store_url: str
    tiktok_code: Optional[str] = None
    keywords: List[str] = []

class ReferralData(BaseModel):
    source_type: str = "unknown"  # meta_ad, tiktok_ad, organic, etc.
    source_id: Optional[str] = None
    headline: Optional[str] = None
    body: Optional[str] = None
    media_type: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    matched_product_id: Optional[str] = None

class Order(BaseModel):
    id: Optional[int] = None
    customer_phone: str
    customer_name: Optional[str] = None
    province: Optional[str] = None
    address: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_price: Optional[int] = None
    quantity: int = 1
    total_amount: Optional[int] = None
    source: str = "organic"  # meta_ad, tiktok_ad, direct
    status: str = "pending"  # pending, confirmed, cancelled
    created_at: Optional[str] = None

class IncomingMessage(BaseModel):
    from_number: str
    message_id: str
    timestamp: str
    text: Optional[str] = None
    button_reply_id: Optional[str] = None
    list_reply_id: Optional[str] = None
    referral: Optional[ReferralData] = None
