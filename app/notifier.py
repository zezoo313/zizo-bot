import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.models import Order

logger = logging.getLogger("notifier")

def notify_new_order(order: Order, order_id: int):
    """
    إرسال إشعار فوري لصاحب المتجر بالطلب الجديد إلى dandana600@gmail.com
    """
    subject = f"🔔 طلب جديد #{order_id} - متجر زيزو ({order.customer_name or 'عميل جديد'})"

    html_content = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px;">
        <h2 style="color: #5b45e0; border-bottom: 2px solid #5b45e0; padding-bottom: 10px;">🎉 طلب شراء جديد من واتساب!</h2>
        <p>تم استلام طلب جديد عبر بوت متجر زيزو:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <tr style="background: #f8f7ff;">
                <td style="padding: 8px; font-weight: bold; width: 35%;">رقم الطلب:</td>
                <td style="padding: 8px;">#{order_id}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">اسم الزبون:</td>
                <td style="padding: 8px;">{order.customer_name or 'لم يحدد'}</td>
            </tr>
            <tr style="background: #f8f7ff;">
                <td style="padding: 8px; font-weight: bold;">رقم هاتف الزبون:</td>
                <td style="padding: 8px;"><a href="tel:{order.customer_phone}">{order.customer_phone}</a> (<a href="https://wa.me/{order.customer_phone}">مراسلة واتساب</a>)</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">المحافظة والمنطقة:</td>
                <td style="padding: 8px;">{order.province or ''} - {order.address or ''}</td>
            </tr>
            <tr style="background: #f8f7ff;">
                <td style="padding: 8px; font-weight: bold;">المنتج المطلوب:</td>
                <td style="padding: 8px;">{order.product_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">الكمية:</td>
                <td style="padding: 8px;">{order.quantity}</td>
            </tr>
            <tr style="background: #f8f7ff;">
                <td style="padding: 8px; font-weight: bold;">إجمالي المبلغ:</td>
                <td style="padding: 8px; font-weight: bold; color: #e11d48;">{order.total_amount:,} دينار عراقي</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">مصدر الزبون:</td>
                <td style="padding: 8px;">{order.source}</td>
            </tr>
        </table>

        <div style="margin-top: 25px; padding: 12px; background: #ecfdf5; border-right: 4px solid #10b981; border-radius: 4px;">
            <strong>طريقة الدفع:</strong> الدفع عند الاستلام داخل العراق 🇮🇶
        </div>
        
        <p style="font-size: 12px; color: #888; margin-top: 20px; text-align: center;">
            تم إرسال هذا التنبيه التلقائي من نظام بوت متجر زيزو
        </p>
    </div>
    """

    logger.info(f"New Order Alert for #{order_id}: {order.customer_name} - {order.product_name} ({order.total_amount} IQD)")

    # إذا تم إعداد بيانات SMTP في .env نقوم بإرسال الإيميل
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USERNAME
            msg["To"] = settings.NOTIFICATION_EMAIL
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USERNAME, settings.NOTIFICATION_EMAIL, msg.as_string())
            logger.info(f"Notification email sent to {settings.NOTIFICATION_EMAIL}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    else:
        logger.info(f"Email notification skipped (No SMTP credentials configured). Order recorded in DB.")
