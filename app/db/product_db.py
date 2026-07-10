import sqlite3
from ..models.product import Product


class ProductDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, name: str, description: str = "", price: float = 0.0,
               stock: int = 0, sort_order: int = 0) -> Product:
        cursor = self.conn.execute(
            "INSERT INTO products (name, description, price, stock, sort_order) VALUES (?, ?, ?, ?, ?)",
            (name, description, price, stock, sort_order),
        )
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, product_id: int) -> Product | None:
        cursor = self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return Product.from_row(row) if row else None

    def update(self, product_id: int, **kwargs) -> Product | None:
        fields = []
        values = []
        for key in ["name", "description", "price", "stock", "is_active", "sort_order"]:
            if key in kwargs:
                fields.append(f"{key} = ?")
                values.append(kwargs[key])
        if not fields:
            return self.get_by_id(product_id)
        fields.append("updated_at = datetime('now')")
        values.append(product_id)
        self.conn.execute(
            f"UPDATE products SET {', '.join(fields)} WHERE id = ?",
            tuple(values),
        )
        return self.get_by_id(product_id)

    def delete(self, product_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return cursor.rowcount > 0

    def list_active(self, offset: int = 0, limit: int = 10) -> list[Product]:
        cursor = self.conn.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [Product.from_row(row) for row in cursor.fetchall()]

    def count_active(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
        return cursor.fetchone()["cnt"]

    def list_all(self, offset: int = 0, limit: int = 50) -> list[Product]:
        cursor = self.conn.execute(
            "SELECT * FROM products ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [Product.from_row(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM products")
        return cursor.fetchone()["cnt"]

    def update_stock(self, product_id: int, delta: int) -> Product | None:
        self.conn.execute(
            "UPDATE products SET stock = stock + ?, updated_at = datetime('now') WHERE id = ?",
            (delta, product_id),
        )
        return self.get_by_id(product_id)
