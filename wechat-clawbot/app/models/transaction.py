import sqlite3


class Transaction:
    TYPE_RECHARGE = "recharge"
    TYPE_PURCHASE = "purchase"

    def __init__(self, id=None, user_id=None, trans_type=None, amount=0.0,
                 balance_before=0.0, balance_after=0.0, description=None,
                 order_id=None, recharge_card_id=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.trans_type = trans_type
        self.amount = amount
        self.balance_before = balance_before
        self.balance_after = balance_after
        self.description = description
        self.order_id = order_id
        self.recharge_card_id = recharge_card_id
        self.created_at = created_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trans_type TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0.0,
                balance_before REAL NOT NULL DEFAULT 0.0,
                balance_after REAL NOT NULL DEFAULT 0.0,
                description TEXT DEFAULT '',
                order_id INTEGER,
                recharge_card_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id, created_at)")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transaction":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            trans_type=row["trans_type"],
            amount=row["amount"],
            balance_before=row["balance_before"],
            balance_after=row["balance_after"],
            description=row["description"],
            order_id=row["order_id"],
            recharge_card_id=row["recharge_card_id"],
            created_at=row["created_at"],
        )
