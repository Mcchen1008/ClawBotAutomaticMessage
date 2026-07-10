import logging
from ..session import UserSession
from ...database import get_db
from ...db.user_db import UserDB
from ...db.product_db import ProductDB
from ...db.card_db import CardDB
from ...db.order_db import OrderDB
from ...db.transaction_db import TransactionDB
from ...models.order import Order
from ...models.transaction import Transaction
from ...config import PAGE_SIZE

logger = logging.getLogger(__name__)


class ProductHandler:
    STATE_HOME = "home"
    STATE_PRODUCT_DETAIL = "product_detail"
    STATE_PRODUCT_BUY_CONFIRM = "product_buy_confirm"

    @staticmethod
    def get_home_page(session: UserSession) -> str:
        with get_db() as conn:
            user_db = UserDB(conn)
            product_db = ProductDB(conn)

            user = user_db.get_by_id(session.user_db_id) if session.user_db_id else None
            balance = user.balance if user else 0.0

            total = product_db.count_active()
            total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if session.page < 1:
                session.page = 1
            elif session.page > total_pages:
                session.page = total_pages

            offset = (session.page - 1) * PAGE_SIZE
            products = product_db.list_active(offset=offset, limit=PAGE_SIZE)

        lines = [
            f"💰 当前余额：{balance:.2f} 元",
            f"📦 商品列表（第 {session.page}/{total_pages} 页）",
            "",
        ]

        for i, p in enumerate(products, 1):
            lines.append(f"{i}. 【{p.name}】- {p.price:.2f}元 (库存:{p.stock})")

        lines.append("")
        lines.append("💡 回复数字选择商品")
        lines.append("📖 指令：p上一页 q下一页 充值 余额 账单 卡密记录")

        return "\n".join(lines)

    @classmethod
    async def handle(cls, session: UserSession, message: str) -> str:
        text = message.strip()

        if session.state == cls.STATE_HOME:
            return await cls._handle_home(session, text)
        elif session.state == cls.STATE_PRODUCT_DETAIL:
            return await cls._handle_product_detail(session, text)
        elif session.state == cls.STATE_PRODUCT_BUY_CONFIRM:
            return await cls._handle_buy_confirm(session, text)

        return cls.get_home_page(session)

    @classmethod
    async def _handle_home(cls, session: UserSession, text: str) -> str:
        if text.lower() == "p":
            if session.page > 1:
                session.page -= 1
            return cls.get_home_page(session)
        elif text.lower() == "q":
            session.page += 1
            return cls.get_home_page(session)
        elif text.isdigit():
            idx = int(text)
            if idx < 1 or idx > PAGE_SIZE:
                return "序号不正确，请重新输入"

            with get_db() as conn:
                product_db = ProductDB(conn)
                offset = (session.page - 1) * PAGE_SIZE
                products = product_db.list_active(offset=offset, limit=PAGE_SIZE)

                if idx > len(products):
                    return "序号不正确，请重新输入"

                product = products[idx - 1]
                session.selected_product_id = product.id
                session.state = cls.STATE_PRODUCT_DETAIL

                return cls._format_product_detail(product)

        return cls.get_home_page(session)

    @staticmethod
    def _format_product_detail(product) -> str:
        return (
            f"📦 商品详情\n"
            f"━━━━━━━━━━━━━\n"
            f"名称：{product.name}\n"
            f"价格：{product.price:.2f} 元\n"
            f"库存：{product.stock} 件\n\n"
            f"商品介绍：\n{product.description or '暂无介绍'}\n"
            f"━━━━━━━━━━━━━\n\n"
            f"回复「购买」立即下单\n"
            f"回复「返回」回到商品列表"
        )

    @classmethod
    async def _handle_product_detail(cls, session: UserSession, text: str) -> str:
        if text in ["返回", "退出"]:
            session.state = cls.STATE_HOME
            session.selected_product_id = None
            return cls.get_home_page(session)
        elif text == "购买":
            if not session.selected_product_id:
                session.state = cls.STATE_HOME
                return cls.get_home_page(session)

            with get_db() as conn:
                product_db = ProductDB(conn)
                product = product_db.get_by_id(session.selected_product_id)
                user_db = UserDB(conn)
                user = user_db.get_by_id(session.user_db_id)

                if not product or not product.is_active:
                    session.state = cls.STATE_HOME
                    session.selected_product_id = None
                    return "商品已下架\n\n" + cls.get_home_page(session)

                if product.stock <= 0:
                    return "商品库存不足，请选择其他商品"

                if user.balance < product.price:
                    return (
                        f"余额不足！\n"
                        f"商品价格：{product.price:.2f} 元\n"
                        f"当前余额：{user.balance:.2f} 元\n"
                        f"差额：{product.price - user.balance:.2f} 元\n\n"
                        f"回复「充值」进行充值"
                    )

            session.state = cls.STATE_PRODUCT_BUY_CONFIRM
            return (
                f"确认购买【{product.name}】？\n"
                f"价格：{product.price:.2f} 元\n"
                f"当前余额：{user.balance:.2f} 元\n\n"
                f"回复「确认」完成购买\n"
                f"回复「取消」返回详情"
            )

        return "请回复「购买」或「返回」"

    @classmethod
    async def _handle_buy_confirm(cls, session: UserSession, text: str) -> str:
        if text in ["取消", "返回"]:
            session.state = cls.STATE_PRODUCT_DETAIL
            with get_db() as conn:
                product_db = ProductDB(conn)
                product = product_db.get_by_id(session.selected_product_id)
                if product:
                    return cls._format_product_detail(product)
            return cls.get_home_page(session)

        if text != "确认":
            return "请回复「确认」完成购买，或「取消」返回"

        if not session.selected_product_id or not session.user_db_id:
            session.state = cls.STATE_HOME
            return cls.get_home_page(session)

        try:
            with get_db() as conn:
                product_db = ProductDB(conn)
                card_db = CardDB(conn)
                order_db = OrderDB(conn)
                trans_db = TransactionDB(conn)
                user_db = UserDB(conn)

                product = product_db.get_by_id(session.selected_product_id)
                user = user_db.get_by_id(session.user_db_id)

                if not product or not product.is_active:
                    session.state = cls.STATE_HOME
                    session.selected_product_id = None
                    return "商品已下架\n\n" + cls.get_home_page(session)

                if product.stock <= 0:
                    session.state = cls.STATE_PRODUCT_DETAIL
                    return "商品库存不足"

                if user.balance < product.price:
                    session.state = cls.STATE_PRODUCT_DETAIL
                    return "余额不足，请先充值"

                card = card_db.get_available_product_card(product.id)
                if not card:
                    session.state = cls.STATE_PRODUCT_DETAIL
                    return "商品卡密已售完，请稍后再试"

                order = order_db.create(
                    user_id=user.id,
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                )

                balance_before = user.balance
                updated_user = user_db.decrease_balance(user.id, product.price)
                if not updated_user:
                    order_db.update_status(order.id, Order.STATUS_FAILED)
                    session.state = cls.STATE_PRODUCT_DETAIL
                    return "余额不足，请先充值"

                balance_after = updated_user.balance

                used_card = card_db.use_product_card(card.id, user.id, order.id)
                if not used_card:
                    user_db.increase_balance(user.id, product.price)
                    order_db.update_status(order.id, Order.STATUS_FAILED)
                    session.state = cls.STATE_PRODUCT_DETAIL
                    return "商品卡密已售完，请稍后再试"

                card = used_card

                order_db.update_status(order.id, Order.STATUS_COMPLETED, card.id)

                trans_db.create(
                    user_id=user.id,
                    trans_type=Transaction.TYPE_PURCHASE,
                    amount=product.price,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=f"购买商品：{product.name}",
                    order_id=order.id,
                )

            session.state = cls.STATE_HOME
            session.selected_product_id = None

            return (
                f"✅ 购买成功！\n"
                f"━━━━━━━━━━━━━\n"
                f"商品：{product.name}\n"
                f"价格：{product.price:.2f} 元\n"
                f"剩余余额：{balance_after:.2f} 元\n\n"
                f"🎁 卡密信息：\n"
                f"卡号：{card.card_code}\n"
                f"卡密：{card.card_secret}\n"
                f"━━━━━━━━━━━━━\n\n"
                f"请妥善保管您的卡密！"
            )
        except Exception as e:
            logger.error(f"购买失败: {e}", exc_info=True)
            session.state = cls.STATE_PRODUCT_DETAIL
            return "购买失败，请稍后重试"
