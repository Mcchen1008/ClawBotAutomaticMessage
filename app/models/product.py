import sqlite3


class Product:
    def __init__(self, id=None, name=None, description=None, price=0.0,
                 stock=0, is_active=True, sort_order=0, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.is_active = is_active
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                price REAL NOT NULL DEFAULT 0.0,
                stock INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active, sort_order)")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Product":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            is_active=bool(row["is_active"]),
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
