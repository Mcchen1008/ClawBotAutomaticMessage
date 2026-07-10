import logging
from ..session import UserSession
from ...database import get_db
from ...db.user_db import UserDB
from ...db.card_db import CardDB
from ...db.transaction_db import TransactionDB
from ...models.transaction import Transaction

logger = logging.getLogger(__name__)


class RechargeHandler:
    STATE_RECHARGE_INPUT = "recharge_input"

    @staticmethod
    def get_recharge_menu() -> str:
        return (
            "💳 充值中心\n"
            "━━━━━━━━━━━━━\n\n"
            "请输入充值卡密：\n\n"
            "回复「返回」退出充值"
        )

    @classmethod
    async def handle(cls, session: UserSession, message: str) -> str:
        text = message.strip()

        if text in ["返回", "退出", "0"]:
            session.state = "home"
            from .product_handler import ProductHandler
            return ProductHandler.get_home_page(session)

        return await cls._handle_recharge(session, text)

    @classmethod
    async def _handle_recharge(cls, session: UserSession, card_code: str) -> str:
        if not session.user_db_id:
            session.state = "auth_select"
            from .auth_handler import AuthHandler
            return AuthHandler.get_auth_menu()

        card_code = card_code.strip()
        if len(card_code) < 4:
            return "充值卡密格式不正确，请重新输入：\n\n回复「返回」退出充值"

        try:
            with get_db() as conn:
                card_db = CardDB(conn)
                trans_db = TransactionDB(conn)
                user_db = UserDB(conn)

                card = card_db.get_recharge_card_by_code(card_code)

                if not card:
                    return "❌ 充值卡密不存在，请检查后重新输入：\n\n回复「返回」退出充值"

                if card.is_used:
                    return "❌ 该充值卡密已被使用\n\n回复「返回」退出充值"

                user = user_db.get_by_id(session.user_db_id)
                balance_before = user.balance

                used = card_db.use_recharge_card(card.id, user.id)
                if not used:
                    return "❌ 该充值卡密已被使用\n\n回复「返回」退出充值"

                updated_user = user_db.increase_balance(user.id, card.amount)
                balance_after = updated_user.balance

                trans_db.create(
                    user_id=user.id,
                    trans_type=Transaction.TYPE_RECHARGE,
                    amount=card.amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=f"充值卡密核销",
                    recharge_card_id=card.id,
                )

            session.state = "home"

            return (
                f"✅ 充值成功！\n"
                f"━━━━━━━━━━━━━\n"
                f"充值金额：{card.amount:.2f} 元\n"
                f"充值前余额：{balance_before:.2f} 元\n"
                f"充值后余额：{balance_after:.2f} 元\n"
                f"━━━━━━━━━━━━━\n\n"
                f"回复「主页」查看商品"
            )
        except Exception as e:
            logger.error(f"充值失败: {e}", exc_info=True)
            return "充值失败，请稍后重试\n\n回复「返回」退出充值"
