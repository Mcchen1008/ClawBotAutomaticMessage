import sqlite3
from ..models.transaction import Transaction


class TransactionDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, user_id: int, trans_type: str, amount: float,
               balance_before: float, balance_after: float, description: str = "",
               order_id: int = None, recharge_card_id: int = None) -> Transaction:
        cursor = self.conn.execute(
            """INSERT INTO transactions 
               (user_id, trans_type, amount, balance_before, balance_after, description, order_id, recharge_card_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, trans_type, amount, balance_before, balance_after, description, order_id, recharge_card_id),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, trans_id: int) -> Transaction | None:
        cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (trans_id,))
        row = cursor.fetchone()
        return Transaction.from_row(row) if row else None

    def list_by_user(self, user_id: int, offset: int = 0, limit: int = 20) -> list[Transaction]:
        cursor = self.conn.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        return [Transaction.from_row(row) for row in cursor.fetchall()]

    def count_by_user(self, user_id: int) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE user_id = ?", (user_id,))
        return cursor.fetchone()["cnt"]

    def list_all(self, offset: int = 0, limit: int = 50) -> list[Transaction]:
        cursor = self.conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [Transaction.from_row(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM transactions")
        return cursor.fetchone()["cnt"]

    def get_statistics(self) -> dict:
        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total_recharge FROM transactions WHERE trans_type = 'recharge'"
        )
        total_recharge = cursor.fetchone()["total_recharge"]

        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total_purchase FROM transactions WHERE trans_type = 'purchase'"
        )
        total_purchase = cursor.fetchone()["total_purchase"]

        cursor = self.conn.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()["user_count"]

        cursor = self.conn.execute("SELECT COUNT(*) as order_count FROM orders WHERE status = 'completed'")
        order_count = cursor.fetchone()["order_count"]

        return {
            "total_recharge": total_recharge,
            "total_purchase": total_purchase,
            "user_count": user_count,
            "order_count": order_count,
        }
