import logging
from .session import SessionManager, UserSession
from .client import ClawBotClient
from .handlers import AuthHandler, ProductHandler, RechargeHandler, QueryHandler

logger = logging.getLogger(__name__)


class MessageDispatcher:
    def __init__(self, session_manager: SessionManager, bot_client: ClawBotClient):
        self.session_manager = session_manager
        self.bot_client = bot_client
        self.auth_handler = AuthHandler()
        self.product_handler = ProductHandler()
        self.recharge_handler = RechargeHandler()
        self.query_handler = QueryHandler()

    async def dispatch(self, message: dict):
        try:
            from_user, content = self._parse_message(message)
            if not from_user or not content:
                return

            session = self.session_manager.get(from_user)
            response = await self._process_message(session, content)

            if response:
                await self.bot_client.send_message(from_user, response)
        except Exception as e:
            logger.error(f"消息处理异常: {e}", exc_info=True)

    @staticmethod
    def _parse_message(message: dict) -> tuple[str, str]:
        from_user = ""
        content = ""

        if "from_user" in message:
            from_user = message["from_user"]
        elif "FromUserName" in message:
            from_user = message["FromUserName"]
        elif "sender" in message:
            from_user = message["sender"]

        if "content" in message:
            content = message["content"]
        elif "Content" in message:
            content = message["Content"]
        elif "text" in message:
            content = message["text"]

        return from_user, content.strip() if content else ""

    async def _process_message(self, session: UserSession, content: str) -> str:
        if not content:
            return ""

        auth_states = {
            "auth_select",
            "register_password",
            "login_userid",
            "login_password",
        }

        if session.state in auth_states:
            return await AuthHandler.handle(session, content, session.wechat_id)

        if session.state in ("home", "product_detail", "product_buy_confirm",
                            "recharge_input", "bill_list", "card_list"):
            if not session.user_db_id:
                session.go_home()
                return AuthHandler.get_auth_menu()

        if content in ["退出登录"]:
            return AuthHandler.logout(session)

        if content in ["主页", "菜单", "帮助"]:
            session.state = "home"
            session.page = 1
            session.selected_product_id = None
            return ProductHandler.get_home_page(session)

        if content in ["说明", "指令"]:
            return QueryHandler.get_help()

        if content in ["客服", "人工"]:
            return QueryHandler.get_service()

        if content in ["重置"]:
            session.go_home()
            return ProductHandler.get_home_page(session)

        if content == "充值":
            session.state = "recharge_input"
            return RechargeHandler.get_recharge_menu()

        if content == "余额":
            return QueryHandler.get_balance(session)

        if content == "账单":
            session.state = "bill_list"
            session.page = 1
            return QueryHandler.get_bill_list(session)

        if content == "卡密记录":
            session.state = "card_list"
            session.page = 1
            return QueryHandler.get_card_list(session)

        if session.state == "recharge_input":
            return await RechargeHandler.handle(session, content)

        if session.state == "bill_list":
            return await QueryHandler.handle_bill(session, content)

        if session.state == "card_list":
            return await QueryHandler.handle_card(session, content)

        if session.state in ("home", "product_detail", "product_buy_confirm"):
            return await ProductHandler.handle(session, content)

        session.go_home()
        return ProductHandler.get_home_page(session)
