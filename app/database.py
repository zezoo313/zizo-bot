import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.config import settings
from app.models import Order

def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # جدول الجلسات والمحادثات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        phone TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        data_json TEXT DEFAULT '{}',
        last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # جدول الطلبات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_phone TEXT NOT NULL,
        customer_name TEXT,
        province TEXT,
        address TEXT,
        product_id TEXT,
        product_name TEXT,
        product_price INTEGER,
        quantity INTEGER DEFAULT 1,
        total_amount INTEGER,
        source TEXT DEFAULT 'organic',
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # جدول سجل الرسائل
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        direction TEXT NOT NULL,
        content TEXT,
        source TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

def get_session(phone: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT state, data_json FROM sessions WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "state": row["state"],
            "data": json.loads(row["data_json"]) if row["data_json"] else {}
        }
    return {"state": "NEW", "data": {}}

def save_session(phone: str, state: str, data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (phone, state, data_json, last_interaction)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(phone) DO UPDATE SET
            state = excluded.state,
            data_json = excluded.data_json,
            last_interaction = CURRENT_TIMESTAMP;
    """, (phone, state, json.dumps(data, ensure_ascii=False)))
    conn.commit()
    conn.close()

def reset_session(phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE phone = ?", (phone,))
    conn.commit()
    conn.close()

def create_order(order: Order) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (
            customer_phone, customer_name, province, address,
            product_id, product_name, product_price, quantity,
            total_amount, source, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order.customer_phone, order.customer_name, order.province, order.address,
        order.product_id, order.product_name, order.product_price, order.quantity,
        order.total_amount, order.source, order.status
    ))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_all_orders() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    orders = [dict(row) for row in rows]
    conn.close()
    return orders

def log_message(phone: str, direction: str, content: str, source: str = "general"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message_logs (phone, direction, content, source)
            VALUES (?, ?, ?, ?)
        """, (phone, direction, content, source))
        conn.commit()
        conn.close()
    except Exception:
        pass
