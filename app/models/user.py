import sqlite3
import bcrypt


class User:
    def __init__(self, id=None, user_id=None, password_hash=None, balance=0.0,
                 wechat_id=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.password_hash = password_hash
        self.balance = balance
        self.wechat_id = wechat_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                wechat_id TEXT UNIQUE,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_wechat_id ON users(wechat_id)")

    @staticmethod
    def hash_password(password: str) -> str:
        if isinstance(password, str):
            password = password.encode("utf-8")
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, password: str) -> bool:
        if isinstance(password, str):
            password = password.encode("utf-8")
        if isinstance(self.password_hash, str):
            stored_hash = self.password_hash.encode("utf-8")
        else:
            stored_hash = self.password_hash
        try:
            return bcrypt.checkpw(password, stored_hash)
        except Exception:
            return False

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            password_hash=row["password_hash"],
            balance=row["balance"],
            wechat_id=row["wechat_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
