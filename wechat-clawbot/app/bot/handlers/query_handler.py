import logging
from ..session import UserSession
from ...database import get_db
from ...db.user_db import UserDB
from ...db.card_db import CardDB
from ...db.transaction_db import TransactionDB
from ...config import PAGE_SIZE

logger = logging.getLogger(__name__)


class QueryHandler:
    STATE_BILL_LIST = "bill_list"
    STATE_CARD_LIST = "card_list"

    @staticmethod
    def get_balance(session: UserSession) -> str:
        with get_db() as conn:
            user_db = UserDB(conn)
            user = user_db.get_by_id(session.user_db_id)
            balance = user.balance if user else 0.0

        return (
            f"💰 账户余额\n"
            f"━━━━━━━━━━━━━\n"
            f"当前余额：{balance:.2f} 元\n"
            f"━━━━━━━━━━━━━\n\n"
            f"回复「充值」进行充值\n"
            f"回复「账单」查看流水\n"
            f"回复「卡密记录」查看购买记录"
        )

    @staticmethod
    def get_bill_list(session: UserSession) -> str:
        with get_db() as conn:
            trans_db = TransactionDB(conn)

            total = trans_db.count_by_user(session.user_db_id)
            total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if session.page < 1:
                session.page = 1
            elif session.page > total_pages:
                session.page = total_pages

            offset = (session.page - 1) * PAGE_SIZE
            transactions = trans_db.list_by_user(session.user_db_id, offset=offset, limit=PAGE_SIZE)

        lines = [
            f"📋 账单明细（第 {session.page}/{total_pages} 页）",
            "━━━━━━━━━━━━━",
        ]

        if not transactions:
            lines.append("暂无账单记录")
        else:
            type_map = {"recharge": "充值", "purchase": "消费"}
            for t in transactions:
                t_type = type_map.get(t.trans_type, t.trans_type)
                sign = "+" if t.trans_type == "recharge" else "-"
                lines.append(f"[{t.created_at[:16]}] {t_type} {sign}{t.amount:.2f}元")
                lines.append(f"  {t.description}")

        lines.append("━━━━━━━━━━━━━")
        lines.append("💡 p上一页 q下一页 返回回到主页")

        return "\n".join(lines)

    @staticmethod
    def get_card_list(session: UserSession) -> str:
        with get_db() as conn:
            card_db = CardDB(conn)

            total = card_db.count_user_product_cards(session.user_db_id)
            total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if session.page < 1:
                session.page = 1
            elif session.page > total_pages:
                session.page = total_pages

            offset = (session.page - 1) * PAGE_SIZE
            cards = card_db.get_user_product_cards(session.user_db_id, offset=offset, limit=PAGE_SIZE)

        lines = [
            f"🎫 卡密记录（第 {session.page}/{total_pages} 页）",
            "━━━━━━━━━━━━━",
        ]

        if not cards:
            lines.append("暂无卡密记录")
        else:
            for i, c in enumerate(cards, 1):
                lines.append(f"{i}. [{c.used_at[:16] if c.used_at else ''}]")
                lines.append(f"   卡号：{c.card_code}")
                lines.append(f"   卡密：{c.card_secret}")

        lines.append("━━━━━━━━━━━━━")
        lines.append("💡 p上一页 q下一页 返回回到主页")

        return "\n".join(lines)

    @classmethod
    async def handle_bill(cls, session: UserSession, message: str) -> str:
        text = message.strip()

        if text in ["返回", "退出"]:
            session.state = "home"
            session.page = 1
            from .product_handler import ProductHandler
            return ProductHandler.get_home_page(session)
        elif text.lower() == "p":
            if session.page > 1:
                session.page -= 1
            return cls.get_bill_list(session)
        elif text.lower() == "q":
            session.page += 1
            return cls.get_bill_list(session)

        return cls.get_bill_list(session)

    @classmethod
    async def handle_card(cls, session: UserSession, message: str) -> str:
        text = message.strip()

        if text in ["返回", "退出"]:
            session.state = "home"
            session.page = 1
            from .product_handler import ProductHandler
            return ProductHandler.get_home_page(session)
        elif text.lower() == "p":
            if session.page > 1:
                session.page -= 1
            return cls.get_card_list(session)
        elif text.lower() == "q":
            session.page += 1
            return cls.get_card_list(session)

        return cls.get_card_list(session)

    @staticmethod
    def get_help() -> str:
        return (
            "📖 指令说明\n"
            "━━━━━━━━━━━━━\n\n"
            "【主页指令】\n"
            "主页/菜单/帮助 - 打开商品面板\n\n"
            "【账户操作】\n"
            "充值 - 进入充值通道\n"
            "余额 - 查看账户余额\n"
            "账单 - 查看消费/充值流水\n"
            "卡密记录 - 查看已购买的卡密\n\n"
            "【浏览操作】\n"
            "p - 上一页\n"
            "q - 下一页\n"
            "数字 - 选择商品\n\n"
            "【其他】\n"
            "退出登录 - 退出当前账号\n"
            "说明/指令 - 查看帮助\n"
            "客服/人工 - 联系客服\n\n"
            "━━━━━━━━━━━━━"
        )

    @staticmethod
    def get_service() -> str:
        return (
            "👤 联系客服\n"
            "━━━━━━━━━━━━━\n\n"
            "工作时间：9:00 - 22:00\n\n"
            "如有问题请留言，\n"
            "我们会尽快回复您。\n\n"
            "━━━━━━━━━━━━━"
        )
