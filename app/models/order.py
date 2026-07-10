import sqlite3


class Order:
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __init__(self, id=None, order_no=None, user_id=None, product_id=None,
                 product_name=None, price=0.0, status=None, card_id=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.order_no = order_no
        self.user_id = user_id
        self.product_id = product_id
        self.product_name = product_name
        self.price = price
        self.status = status
        self.card_id = card_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'pending',
                card_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_no ON orders(order_no)")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Order":
        return cls(
            id=row["id"],
            order_no=row["order_no"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            price=row["price"],
            status=row["status"],
            card_id=row["card_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
