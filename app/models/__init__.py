from .user import User
from .product import Product
from .card import ProductCard, RechargeCard
from .order import Order
from .transaction import Transaction

__all__ = [
    "User",
    "Product",
    "ProductCard",
    "RechargeCard",
    "Order",
    "Transaction",
]


def create_tables(conn):
    User.create_table(conn)
    Product.create_table(conn)
    ProductCard.create_table(conn)
    RechargeCard.create_table(conn)
    Order.create_table(conn)
    Transaction.create_table(conn)
