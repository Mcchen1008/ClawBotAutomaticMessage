import sqlite3
from ..models.card import ProductCard, RechargeCard


class CardDB:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_product_card(self, product_id: int, card_code: str, card_secret: str = "") -> ProductCard:
        cursor = self.conn.execute(
            "INSERT INTO product_cards (product_id, card_code, card_secret) VALUES (?, ?, ?)",
            (product_id, card_code, card_secret),
        )
        self.conn.execute(
            "UPDATE products SET stock = stock + 1, updated_at = datetime('now') WHERE id = ?",
            (product_id,),
        )
        return self.get_product_card_by_id(cursor.lastrowid)

    def batch_add_product_cards(self, product_id: int, cards: list[tuple[str, str]]) -> int:
        count = 0
        for card_code, card_secret in cards:
            self.conn.execute(
                "INSERT OR IGNORE INTO product_cards (product_id, card_code, card_secret) VALUES (?, ?, ?)",
                (product_id, card_code, card_secret),
            )
            count += 1
        self.conn.execute(
            "UPDATE products SET stock = (SELECT COUNT(*) FROM product_cards WHERE product_id = ? AND is_used = 0), updated_at = datetime('now') WHERE id = ?",
            (product_id, product_id),
        )
        return count

    def get_product_card_by_id(self, card_id: int) -> ProductCard | None:
        cursor = self.conn.execute("SELECT * FROM product_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        return ProductCard.from_row(row) if row else None

    def get_available_product_card(self, product_id: int) -> ProductCard | None:
        cursor = self.conn.execute(
            "SELECT * FROM product_cards WHERE product_id = ? AND is_used = 0 ORDER BY id ASC LIMIT 1",
            (product_id,),
        )
        row = cursor.fetchone()
        return ProductCard.from_row(row) if row else None

    def use_product_card(self, card_id: int, user_id: int, order_id: int) -> ProductCard | None:
        cursor = self.conn.execute(
            "UPDATE product_cards SET is_used = 1, used_by = ?, used_at = datetime('now'), order_id = ? "
            "WHERE id = ? AND is_used = 0",
            (user_id, order_id, card_id),
        )
        if cursor.rowcount == 0:
            return None
        card = self.get_product_card_by_id(card_id)
        if card:
            self.conn.execute(
                "UPDATE products SET stock = MAX(0, stock - 1), updated_at = datetime('now') WHERE id = ?",
                (card.product_id,),
            )
        return card

    def list_product_cards(self, product_id: int = None, is_used: bool = None,
                           offset: int = 0, limit: int = 50) -> list[ProductCard]:
        sql = "SELECT * FROM product_cards WHERE 1=1"
        params = []
        if product_id is not None:
            sql += " AND product_id = ?"
            params.append(product_id)
        if is_used is not None:
            sql += " AND is_used = ?"
            params.append(1 if is_used else 0)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = self.conn.execute(sql, tuple(params))
        return [ProductCard.from_row(row) for row in cursor.fetchall()]

    def count_product_cards(self, product_id: int = None, is_used: bool = None) -> int:
        sql = "SELECT COUNT(*) as cnt FROM product_cards WHERE 1=1"
        params = []
        if product_id is not None:
            sql += " AND product_id = ?"
            params.append(product_id)
        if is_used is not None:
            sql += " AND is_used = ?"
            params.append(1 if is_used else 0)
        cursor = self.conn.execute(sql, tuple(params))
        return cursor.fetchone()["cnt"]

    def add_recharge_card(self, card_code: str, amount: float) -> RechargeCard:
        cursor = self.conn.execute(
            "INSERT INTO recharge_cards (card_code, amount) VALUES (?, ?)",
            (card_code, amount),
        )
        return self.get_recharge_card_by_id(cursor.lastrowid)

    def batch_add_recharge_cards(self, cards: list[tuple[str, float]]) -> int:
        count = 0
        for card_code, amount in cards:
            self.conn.execute(
                "INSERT OR IGNORE INTO recharge_cards (card_code, amount) VALUES (?, ?)",
                (card_code, amount),
            )
            count += 1
        return count

    def get_recharge_card_by_id(self, card_id: int) -> RechargeCard | None:
        cursor = self.conn.execute("SELECT * FROM recharge_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        return RechargeCard.from_row(row) if row else None

    def get_recharge_card_by_code(self, card_code: str) -> RechargeCard | None:
        cursor = self.conn.execute("SELECT * FROM recharge_cards WHERE card_code = ?", (card_code,))
        row = cursor.fetchone()
        return RechargeCard.from_row(row) if row else None

    def use_recharge_card(self, card_id: int, user_id: int) -> RechargeCard | None:
        cursor = self.conn.execute(
            "UPDATE recharge_cards SET is_used = 1, used_by = ?, used_at = datetime('now') "
            "WHERE id = ? AND is_used = 0",
            (user_id, card_id),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_recharge_card_by_id(card_id)

    def list_recharge_cards(self, is_used: bool = None,
                            offset: int = 0, limit: int = 50) -> list[RechargeCard]:
        sql = "SELECT * FROM recharge_cards WHERE 1=1"
        params = []
        if is_used is not None:
            sql += " AND is_used = ?"
            params.append(1 if is_used else 0)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = self.conn.execute(sql, tuple(params))
        return [RechargeCard.from_row(row) for row in cursor.fetchall()]

    def count_recharge_cards(self, is_used: bool = None) -> int:
        sql = "SELECT COUNT(*) as cnt FROM recharge_cards WHERE 1=1"
        params = []
        if is_used is not None:
            sql += " AND is_used = ?"
            params.append(1 if is_used else 0)
        cursor = self.conn.execute(sql, tuple(params))
        return cursor.fetchone()["cnt"]

    def get_user_product_cards(self, user_id: int, offset: int = 0, limit: int = 20) -> list[ProductCard]:
        cursor = self.conn.execute(
            "SELECT * FROM product_cards WHERE used_by = ? ORDER BY used_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        return [ProductCard.from_row(row) for row in cursor.fetchall()]

    def count_user_product_cards(self, user_id: int) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM product_cards WHERE used_by = ?",
            (user_id,),
        )
        return cursor.fetchone()["cnt"]
