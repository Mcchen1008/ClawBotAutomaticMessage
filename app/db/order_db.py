import sqlite3
import uuid
from ..models.order import Order


class OrderDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _generate_order_no() -> str:
        return "ORD" + uuid.uuid4().hex[:16].upper()

    def create(self, user_id: int, product_id: int, product_name: str, price: float) -> Order:
        order_no = self._generate_order_no()
        cursor = self.conn.execute(
            "INSERT INTO orders (order_no, user_id, product_id, product_name, price, status) VALUES (?, ?, ?, ?, ?, ?)",
            (order_no, user_id, product_id, product_name, price, Order.STATUS_PENDING),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, order_id: int) -> Order | None:
        cursor = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return Order.from_row(row) if row else None

    def get_by_order_no(self, order_no: str) -> Order | None:
        cursor = self.conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,))
        row = cursor.fetchone()
        return Order.from_row(row) if row else None

    def update_status(self, order_id: int, status: str, card_id: int = None) -> Order | None:
        if card_id is not None:
            self.conn.execute(
                "UPDATE orders SET status = ?, card_id = ?, updated_at = datetime('now') WHERE id = ?",
                (status, card_id, order_id),
            )
        else:
            self.conn.execute(
                "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, order_id),
            )
        return self.get_by_id(order_id)

    def list_by_user(self, user_id: int, offset: int = 0, limit: int = 20) -> list[Order]:
        cursor = self.conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        return [Order.from_row(row) for row in cursor.fetchall()]

    def count_by_user(self, user_id: int) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = ?", (user_id,))
        return cursor.fetchone()["cnt"]

    def list_all(self, offset: int = 0, limit: int = 50) -> list[Order]:
        cursor = self.conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [Order.from_row(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM orders")
        return cursor.fetchone()["cnt"]
