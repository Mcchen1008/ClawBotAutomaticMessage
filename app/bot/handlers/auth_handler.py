import logging
from ..session import UserSession
from ...database import get_db
from ...db.user_db import UserDB

logger = logging.getLogger(__name__)


class AuthHandler:
    STATE_AUTH_SELECT = "auth_select"
    STATE_REGISTER_PASSWORD = "register_password"
    STATE_LOGIN_USERID = "login_userid"
    STATE_LOGIN_PASSWORD = "login_password"

    @staticmethod
    def get_auth_menu() -> str:
        return (
            "欢迎使用虚拟商品自动售卖系统！\n"
            "请选择操作：\n"
            "1. 注册新账号\n"
            "2. 登录已有账号\n\n"
            "回复数字选择操作"
        )

    @classmethod
    async def handle(cls, session: UserSession, message: str, wechat_id: str) -> str:
        text = message.strip()

        if session.state == cls.STATE_AUTH_SELECT:
            return await cls._handle_auth_select(session, text, wechat_id)
        elif session.state == cls.STATE_REGISTER_PASSWORD:
            return await cls._handle_register_password(session, text, wechat_id)
        elif session.state == cls.STATE_LOGIN_USERID:
            return await cls._handle_login_userid(session, text)
        elif session.state == cls.STATE_LOGIN_PASSWORD:
            return await cls._handle_login_password(session, text, wechat_id)

        return cls.get_auth_menu()

    @classmethod
    async def _handle_auth_select(cls, session: UserSession, text: str, wechat_id: str) -> str:
        if text == "1":
            session.state = cls.STATE_REGISTER_PASSWORD
            return "请设置您的登录密码（6-20位）："
        elif text == "2":
            session.state = cls.STATE_LOGIN_USERID
            return "请输入您的数字用户ID："
        else:
            return cls.get_auth_menu()

    @classmethod
    async def _handle_register_password(cls, session: UserSession, text: str, wechat_id: str) -> str:
        password = text.strip()
        if len(password) < 6 or len(password) > 20:
            return "密码长度需为6-20位，请重新输入："

        with get_db() as conn:
            user_db = UserDB(conn)
            user = user_db.create(password=password, wechat_id=wechat_id)

        session.user_db_id = user.id
        session.state = "home"
        session.temp_data.clear()

        return (
            f"注册成功！\n"
            f"您的用户ID：{user.user_id}\n"
            f"请妥善保管您的ID和密码\n\n"
            f"回复「主页」查看商品列表"
        )

    @classmethod
    async def _handle_login_userid(cls, session: UserSession, text: str) -> str:
        user_id = text.strip()
        if not user_id.isdigit():
            return "用户ID必须是数字，请重新输入："

        session.temp_data["login_userid"] = user_id
        session.state = cls.STATE_LOGIN_PASSWORD
        return "请输入您的登录密码："

    @classmethod
    async def _handle_login_password(cls, session: UserSession, text: str, wechat_id: str) -> str:
        user_id = session.temp_data.get("login_userid", "")
        password = text.strip()

        with get_db() as conn:
            user_db = UserDB(conn)
            user = user_db.get_by_user_id(user_id)

            if not user:
                session.state = cls.STATE_LOGIN_USERID
                session.temp_data.clear()
                return "用户ID不存在，请重新输入用户ID："

            if not user.verify_password(password):
                return "密码错误，请重新输入密码："

            if user.wechat_id and user.wechat_id != wechat_id:
                user_db.update_wechat_id(user.id, wechat_id)
            elif not user.wechat_id:
                user_db.update_wechat_id(user.id, wechat_id)

        session.user_db_id = user.id
        session.state = "home"
        session.temp_data.clear()

        return (
            f"登录成功！欢迎回来\n"
            f"用户ID：{user.user_id}\n"
            f"当前余额：{user.balance:.2f} 元\n\n"
            f"回复「主页」查看商品列表"
        )

    @staticmethod
    def logout(session: UserSession) -> str:
        session.reset()
        return "已退出登录\n\n" + AuthHandler.get_auth_menu()
