import sqlite3
from datetime import datetime


class ProductCard:
    def __init__(self, id=None, product_id=None, card_code=None, card_secret=None,
                 is_used=False, used_by=None, used_at=None, order_id=None, created_at=None):
        self.id = id
        self.product_id = product_id
        self.card_code = card_code
        self.card_secret = card_secret
        self.is_used = is_used
        self.used_by = used_by
        self.used_at = used_at
        self.order_id = order_id
        self.created_at = created_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                card_code TEXT NOT NULL,
                card_secret TEXT DEFAULT '',
                is_used INTEGER NOT NULL DEFAULT 0,
                used_by INTEGER,
                used_at TEXT,
                order_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (used_by) REFERENCES users(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_cards_product ON product_cards(product_id, is_used)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_cards_code ON product_cards(card_code)")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ProductCard":
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            card_code=row["card_code"],
            card_secret=row["card_secret"],
            is_used=bool(row["is_used"]),
            used_by=row["used_by"],
            used_at=row["used_at"],
            order_id=row["order_id"],
            created_at=row["created_at"],
        )


class RechargeCard:
    def __init__(self, id=None, card_code=None, amount=0.0, is_used=False,
                 used_by=None, used_at=None, created_at=None):
        self.id = id
        self.card_code = card_code
        self.amount = amount
        self.is_used = is_used
        self.used_by = used_by
        self.used_at = used_at
        self.created_at = created_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recharge_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_code TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL DEFAULT 0.0,
                is_used INTEGER NOT NULL DEFAULT 0,
                used_by INTEGER,
                used_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (used_by) REFERENCES users(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recharge_cards_code ON recharge_cards(card_code)")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "RechargeCard":
        return cls(
            id=row["id"],
            card_code=row["card_code"],
            amount=row["amount"],
            is_used=bool(row["is_used"]),
            used_by=row["used_by"],
            used_at=row["used_at"],
            created_at=row["created_at"],
        )
