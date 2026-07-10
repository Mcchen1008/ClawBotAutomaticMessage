import sqlite3
import random
from ..models.user import User


class UserDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _generate_user_id() -> str:
        return str(random.randint(100000, 999999))

    def create(self, password: str, wechat_id: str = None) -> User:
        for _ in range(10):
            user_id = self._generate_user_id()
            cursor = self.conn.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                break
        else:
            raise RuntimeError("无法生成唯一用户ID")

        password_hash = User.hash_password(password)
        cursor = self.conn.execute(
            "INSERT INTO users (user_id, password_hash, wechat_id) VALUES (?, ?, ?)",
            (user_id, password_hash, wechat_id),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, user_db_id: int) -> User | None:
        cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_db_id,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    def get_by_user_id(self, user_id: str) -> User | None:
        cursor = self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    def get_by_wechat_id(self, wechat_id: str) -> User | None:
        cursor = self.conn.execute("SELECT * FROM users WHERE wechat_id = ?", (wechat_id,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    def update_balance(self, user_db_id: int, new_balance: float) -> User:
        self.conn.execute(
            "UPDATE users SET balance = ?, updated_at = datetime('now') WHERE id = ?",
            (new_balance, user_db_id),
        )
        return self.get_by_id(user_db_id)

    def decrease_balance(self, user_db_id: int, amount: float) -> User | None:
        cursor = self.conn.execute(
            "UPDATE users SET balance = balance - ?, updated_at = datetime('now') "
            "WHERE id = ? AND balance >= ?",
            (amount, user_db_id, amount),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id(user_db_id)

    def increase_balance(self, user_db_id: int, amount: float) -> User | None:
        cursor = self.conn.execute(
            "UPDATE users SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
            (amount, user_db_id),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id(user_db_id)

    def update_wechat_id(self, user_db_id: int, wechat_id: str) -> User:
        self.conn.execute(
            "UPDATE users SET wechat_id = ?, updated_at = datetime('now') WHERE id = ?",
            (wechat_id, user_db_id),
        )
        return self.get_by_id(user_db_id)

    def list_all(self, offset: int = 0, limit: int = 50) -> list[User]:
        cursor = self.conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [User.from_row(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM users")
        return cursor.fetchone()["cnt"]

    def search(self, keyword: str, offset: int = 0, limit: int = 50) -> list[User]:
        like = f"%{keyword}%"
        cursor = self.conn.execute(
            "SELECT * FROM users WHERE user_id LIKE ? OR wechat_id LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (like, like, limit, offset),
        )
        return [User.from_row(row) for row in cursor.fetchall()]

    def count_search(self, keyword: str) -> int:
        like = f"%{keyword}%"
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE user_id LIKE ? OR wechat_id LIKE ?",
            (like, like),
        )
        return cursor.fetchone()["cnt"]

    def adjust_balance(self, user_db_id: int, delta: float) -> User | None:
        cursor = self.conn.execute(
            "UPDATE users SET balance = MAX(0, balance + ?), updated_at = datetime('now') WHERE id = ?",
            (delta, user_db_id),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id(user_db_id)
