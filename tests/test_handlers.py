import sqlite3
import asyncio
from contextlib import contextmanager

import pytest

from app.models import create_tables
from app.db.user_db import UserDB
from app.db.product_db import ProductDB
from app.db.card_db import CardDB
from app.bot.session import UserSession, SessionManager
from app.bot.handlers.auth_handler import AuthHandler
from app.bot.handlers.product_handler import ProductHandler
from app.bot.handlers.recharge_handler import RechargeHandler
from app.bot.handlers.query_handler import QueryHandler


@contextmanager
def fake_db(conn):
    yield conn


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture
def patched_db(monkeypatch, conn):
    monkeypatch.setattr("app.database.get_db", lambda: fake_db(conn))
    monkeypatch.setattr("app.bot.handlers.auth_handler.get_db", lambda: fake_db(conn))
    monkeypatch.setattr("app.bot.handlers.product_handler.get_db", lambda: fake_db(conn))
    monkeypatch.setattr("app.bot.handlers.recharge_handler.get_db", lambda: fake_db(conn))
    monkeypatch.setattr("app.bot.handlers.query_handler.get_db", lambda: fake_db(conn))
    return conn


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_auth_first_contact_shows_menu(patched_db):
    session = UserSession(wechat_id="wx_new")
    assert session.state == "auth_select"
    resp = run(AuthHandler.handle(session, "你好", "wx_new"))
    assert "1. 注册新账号" in resp
    assert "2. 登录已有账号" in resp
    assert session.state == "auth_select"


def test_auth_register_flow(patched_db):
    session = UserSession(wechat_id="wx_reg")
    run(AuthHandler.handle(session, "1", "wx_reg"))
    assert session.state == AuthHandler.STATE_REGISTER_PASSWORD

    resp = run(AuthHandler.handle(session, "mypassword", "wx_reg"))
    assert "注册成功" in resp
    assert session.state == "home"
    assert session.user_db_id is not None


def test_auth_register_password_too_short(patched_db):
    session = UserSession(wechat_id="wx_reg2")
    run(AuthHandler.handle(session, "1", "wx_reg2"))
    resp = run(AuthHandler.handle(session, "123", "wx_reg2"))
    assert "密码长度" in resp
    assert session.state == AuthHandler.STATE_REGISTER_PASSWORD


def test_auth_login_flow_success(patched_db):
    user_db = UserDB(patched_db)
    user = user_db.create(password="pass1234", wechat_id="wx_login")

    session = UserSession(wechat_id="wx_login")
    run(AuthHandler.handle(session, "2", "wx_login"))
    assert session.state == AuthHandler.STATE_LOGIN_USERID

    run(AuthHandler.handle(session, user.user_id, "wx_login"))
    assert session.state == AuthHandler.STATE_LOGIN_PASSWORD

    resp = run(AuthHandler.handle(session, "pass1234", "wx_login"))
    assert "登录成功" in resp
    assert session.state == "home"


def test_auth_login_wrong_password(patched_db):
    user_db = UserDB(patched_db)
    user = user_db.create(password="pass1234")

    session = UserSession(wechat_id="wx_x")
    run(AuthHandler.handle(session, "2", "wx_x"))
    run(AuthHandler.handle(session, user.user_id, "wx_x"))
    resp = run(AuthHandler.handle(session, "wrongpwd", "wx_x"))
    assert "密码错误" in resp
    assert session.state == AuthHandler.STATE_LOGIN_PASSWORD


def test_auth_login_unknown_userid(patched_db):
    session = UserSession(wechat_id="wx_x")
    run(AuthHandler.handle(session, "2", "wx_x"))
    run(AuthHandler.handle(session, "000000", "wx_x"))
    resp = run(AuthHandler.handle(session, "anything", "wx_x"))
    assert "用户ID不存在" in resp
    assert session.state == AuthHandler.STATE_LOGIN_USERID


def test_auth_logout(patched_db):
    session = UserSession(wechat_id="wx_x")
    session.user_db_id = 1
    session.state = "home"
    resp = AuthHandler.logout(session)
    assert "已退出登录" in resp
    assert session.state == "auth_select"
    assert session.user_db_id is None


def test_product_home_page_shows_balance(patched_db):
    user_db = UserDB(patched_db)
    user = user_db.create(password="pw1234")
    user_db.increase_balance(user.id, 88.0)

    product_db = ProductDB(patched_db)
    product_db.create(name="商品A", price=5.0, sort_order=1)

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    session.state = "home"
    text = ProductHandler.get_home_page(session)
    assert "88.00" in text
    assert "商品A" in text


def test_product_buy_full_flow(patched_db):
    user_db = UserDB(patched_db)
    product_db = ProductDB(patched_db)
    card_db = CardDB(patched_db)

    user = user_db.create(password="pw1234")
    user_db.increase_balance(user.id, 100.0)
    product = product_db.create(name="会员卡", price=29.9)
    card_db.add_product_card(product.id, "CARD01", "SECRET01")

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    session.state = "home"

    detail = run(ProductHandler.handle(session, "1"))
    assert "会员卡" in detail
    assert session.state == ProductHandler.STATE_PRODUCT_DETAIL

    confirm = run(ProductHandler.handle(session, "购买"))
    assert "确认购买" in confirm
    assert session.state == ProductHandler.STATE_PRODUCT_BUY_CONFIRM

    result = run(ProductHandler.handle(session, "确认"))
    assert "购买成功" in result
    assert "CARD01" in result
    assert "SECRET01" in result
    assert session.state == "home"

    assert user_db.get_by_id(user.id).balance == 70.1


def test_product_buy_insufficient_balance(patched_db):
    user_db = UserDB(patched_db)
    product_db = ProductDB(patched_db)
    card_db = CardDB(patched_db)

    user = user_db.create(password="pw1234")
    product = product_db.create(name="贵的商品", price=999.0)
    card_db.add_product_card(product.id, "C1", "S1")

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    session.state = "home"
    run(ProductHandler.handle(session, "1"))
    resp = run(ProductHandler.handle(session, "购买"))
    assert "余额不足" in resp


def test_recharge_success(patched_db):
    user_db = UserDB(patched_db)
    card_db = CardDB(patched_db)
    user = user_db.create(password="pw1234")
    card_db.add_recharge_card("RC123", 50.0)

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    session.state = RechargeHandler.STATE_RECHARGE_INPUT

    resp = run(RechargeHandler.handle(session, "RC123"))
    assert "充值成功" in resp
    assert "50.00" in resp
    assert session.state == "home"
    assert user_db.get_by_id(user.id).balance == 50.0


def test_recharge_invalid_card(patched_db):
    user_db = UserDB(patched_db)
    user = user_db.create(password="pw1234")

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    session.state = RechargeHandler.STATE_RECHARGE_INPUT

    resp = run(RechargeHandler.handle(session, "NOTEXIST"))
    assert "不存在" in resp


def test_recharge_return_exits(patched_db):
    session = UserSession(wechat_id="wx_x")
    session.user_db_id = 1
    session.state = RechargeHandler.STATE_RECHARGE_INPUT
    resp = run(RechargeHandler.handle(session, "返回"))
    assert "余额" in resp or "商品" in resp
    assert session.state == "home"


def test_query_balance(patched_db):
    user_db = UserDB(patched_db)
    user = user_db.create(password="pw1234")
    user_db.increase_balance(user.id, 42.5)

    session = UserSession(wechat_id="wx_x")
    session.user_db_id = user.id
    text = QueryHandler.get_balance(session)
    assert "42.50" in text


def test_query_help_and_service():
    assert "主页" in QueryHandler.get_help()
    assert "客服" in QueryHandler.get_service()


def test_session_manager():
    sm = SessionManager()
    s1 = sm.get("wx_a")
    s2 = sm.get("wx_a")
    assert s1 is s2
    assert sm.get("wx_b") is not s1

    s1.state = "home"
    s1.reset()
    assert s1.state == "auth_select"

    sm.remove("wx_a")
    assert sm.get("wx_a") is not s1
