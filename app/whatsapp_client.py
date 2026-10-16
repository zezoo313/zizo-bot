import requests
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("whatsapp_client")

class WhatsAppClient:
    def __init__(self):
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.PHONE_NUMBER_ID
        self.api_version = settings.META_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """إرسال طلب HTTP إلى واتساب كلاود API"""
        # في بيئة التطوير أو عند عدم وجود توكن حقيقي، نسجل فقط بدون تعطيل الخادم
        if not self.token or self.token.startswith("EAAG..."):
            logger.info(f"[SIMULATION - NO TOKEN] Sending to WhatsApp: {json.dumps(payload, ensure_ascii=False)}")
            return {"status": "simulated", "payload": payload}

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=10)
            if response.status_code >= 400:
                logger.error(f"WhatsApp API Error {response.status_code}: {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {"error": str(e)}

    def send_text_message(self, to: str, text: str, preview_url: bool = False) -> Dict[str, Any]:
        """إرسال رسالة نصية عادية"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }
        return self._post(payload)

    def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]], # [{"id": "btn_1", "title": "تأكيد الطلب"}]
        header_text: Optional[str] = None,
        footer_text: Optional[str] = "متجر زيزو - العراق"
    ) -> Dict[str, Any]:
        """إرسال رسالة تفاعلية بأزرار سريعة (حد أقصى 3 أزرار حسب سياسة واتساب)"""
        formatted_buttons = []
        for btn in buttons[:3]:
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"][:20]  # أقصى طول لعنوان الزر في واتساب هو 20 حرف
                }
            })

        action = {"buttons": formatted_buttons}

        interactive: Dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": action
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        return self._post(payload)

    def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_title: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = "متجر زيزو"
    ) -> Dict[str, Any]:
        """إرسال قائمة اختيار تفاعلية (Menu List)"""
        interactive: Dict[str, Any] = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_title[:20],
                "sections": sections
            }
        }
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        return self._post(payload)

    def send_image_message(self, to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """إرسال صورة منتج مع تعليق"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption or ""
            }
        }
        return self._post(payload)

    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """تحديد الرسالة كمقروءة (Blue ticks)"""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        return self._post(payload)

whatsapp_client = WhatsAppClient()
