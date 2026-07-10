import sqlite3
import pytest

from app.models import create_tables
from app.db.user_db import UserDB
from app.db.product_db import ProductDB
from app.db.card_db import CardDB
from app.db.order_db import OrderDB
from app.db.transaction_db import TransactionDB
from app.models.order import Order
from app.models.transaction import Transaction


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    create_tables(conn)
    yield conn
    conn.close()


def test_user_create_and_login(conn):
    user_db = UserDB(conn)
    user = user_db.create(password="secret123", wechat_id="wx_abc")
    assert user.id is not None
    assert user.user_id.isdigit()
    assert len(user.user_id) == 6
    assert user.balance == 0.0
    assert user.verify_password("secret123")
    assert not user.verify_password("wrong")


def test_user_get_methods(conn):
    user_db = UserDB(conn)
    user = user_db.create(password="pw1234", wechat_id="wx_one")
    assert user_db.get_by_id(user.id).user_id == user.user_id
    assert user_db.get_by_user_id(user.user_id).id == user.id
    assert user_db.get_by_wechat_id("wx_one").id == user.id
    assert user_db.get_by_wechat_id("wx_none") is None


def test_user_balance_atomic_operations(conn):
    user_db = UserDB(conn)
    user = user_db.create(password="pw1234")

    increased = user_db.increase_balance(user.id, 100.0)
    assert increased.balance == 100.0

    ok = user_db.decrease_balance(user.id, 30.0)
    assert ok is not None
    assert ok.balance == 70.0

    insufficient = user_db.decrease_balance(user.id, 1000.0)
    assert insufficient is None
    assert user_db.get_by_id(user.id).balance == 70.0

    missing = user_db.decrease_balance(999999, 1.0)
    assert missing is None


def test_user_adjust_balance(conn):
    user_db = UserDB(conn)
    user = user_db.create(password="pw1234")
    user_db.adjust_balance(user.id, 50.0)
    assert user_db.get_by_id(user.id).balance == 50.0
    user_db.adjust_balance(user.id, -20.0)
    assert user_db.get_by_id(user.id).balance == 30.0
    user_db.adjust_balance(user.id, -100.0)
    assert user_db.get_by_id(user.id).balance == 0.0


def test_user_search_and_count(conn):
    user_db = UserDB(conn)
    user_db.create(password="pw1234", wechat_id="wx_alpha")
    user_db.create(password="pw1234", wechat_id="wx_beta")
    assert user_db.count_all() == 2
    assert user_db.count_search("wx_") == 2
    assert user_db.count_search("alpha") == 1
    assert user_db.count_search("nope") == 0
    assert len(user_db.search("wx_")) == 2


def test_product_crud_and_stock(conn):
    product_db = ProductDB(conn)
    p = product_db.create(name="测试商品", description="desc", price=9.9, stock=0, sort_order=1)
    assert p.is_active is True
    assert product_db.get_by_id(p.id).name == "测试商品"

    updated = product_db.update(p.id, price=19.9, is_active=False)
    assert updated.price == 19.9
    assert updated.is_active is False

    assert product_db.count_active() == 0
    product_db.update(p.id, is_active=True)
    assert product_db.count_active() == 1

    product_db.update_stock(p.id, 5)
    assert product_db.get_by_id(p.id).stock == 5
    product_db.update_stock(p.id, -2)
    assert product_db.get_by_id(p.id).stock == 3

    assert product_db.delete(p.id) is True
    assert product_db.get_by_id(p.id) is None


def test_product_card_atomic_use(conn):
    user_db = UserDB(conn)
    product_db = ProductDB(conn)
    card_db = CardDB(conn)
    order_db = OrderDB(conn)

    user = user_db.create(password="pw1234")
    product = product_db.create(name="商品", price=10.0)
    card = card_db.add_product_card(product.id, "CODE1", "SECRET1")
    assert card.is_used is False
    assert product_db.get_by_id(product.id).stock == 1

    order = order_db.create(user.id, product.id, product.name, product.price)

    used = card_db.use_product_card(card.id, user.id, order.id)
    assert used is not None
    assert used.is_used is True

    again = card_db.use_product_card(card.id, user.id, order.id)
    assert again is None

    assert product_db.get_by_id(product.id).stock == 0


def test_recharge_card_atomic_use(conn):
    card_db = CardDB(conn)
    user_db = UserDB(conn)
    user = user_db.create(password="pw1234")
    card = card_db.add_recharge_card("RECHARGE01", 50.0)

    used = card_db.use_recharge_card(card.id, user.id)
    assert used is not None
    assert used.is_used is True

    again = card_db.use_recharge_card(card.id, user.id)
    assert again is None

    assert card_db.get_recharge_card_by_code("RECHARGE01").is_used is True


def test_batch_add_product_cards_updates_stock(conn):
    product_db = ProductDB(conn)
    card_db = CardDB(conn)
    product = product_db.create(name="商品", price=10.0)
    cards = [("A1", "S1"), ("A2", "S2"), ("A3", "S3")]
    count = card_db.batch_add_product_cards(product.id, cards)
    assert count == 3
    assert product_db.get_by_id(product.id).stock == 3
    assert card_db.count_product_cards(product_id=product.id) == 3


def test_batch_add_recharge_cards_ignores_duplicates(conn):
    card_db = CardDB(conn)
    cards = [("R1", 10.0), ("R1", 20.0), ("R2", 30.0)]
    card_db.batch_add_recharge_cards(cards)
    assert card_db.count_recharge_cards() == 2
    card = card_db.get_recharge_card_by_code("R1")
    assert card.amount == 10.0


def test_order_lifecycle(conn):
    user_db = UserDB(conn)
    product_db = ProductDB(conn)
    order_db = OrderDB(conn)
    user = user_db.create(password="pw1234")
    product = product_db.create(name="商品", price=15.0)

    order = order_db.create(user.id, product.id, product.name, product.price)
    assert order.status == Order.STATUS_PENDING
    assert order.order_no.startswith("ORD")

    completed = order_db.update_status(order.id, Order.STATUS_COMPLETED, card_id=99)
    assert completed.status == Order.STATUS_COMPLETED
    assert completed.card_id == 99

    fetched = order_db.get_by_order_no(order.order_no)
    assert fetched.id == order.id
    assert order_db.count_by_user(user.id) == 1


def test_transaction_statistics(conn):
    user_db = UserDB(conn)
    trans_db = TransactionDB(conn)
    user = user_db.create(password="pw1234")
    user_db.increase_balance(user.id, 100.0)

    trans_db.create(
        user_id=user.id, trans_type=Transaction.TYPE_RECHARGE, amount=100.0,
        balance_before=0.0, balance_after=100.0, description="充值",
    )
    user_db.decrease_balance(user.id, 30.0)
    trans_db.create(
        user_id=user.id, trans_type=Transaction.TYPE_PURCHASE, amount=30.0,
        balance_before=100.0, balance_after=70.0, description="消费",
    )

    stats = trans_db.get_statistics()
    assert stats["total_recharge"] == 100.0
    assert stats["total_purchase"] == 30.0
    assert stats["user_count"] == 1
