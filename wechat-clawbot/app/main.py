import asyncio
import logging
import sys
from .config import WEB_HOST, WEB_PORT, LOG_LEVEL
from .database import init_db
from .bot.client import ClawBotClient
from .bot.session import SessionManager
from .bot.dispatcher import MessageDispatcher

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot_client = None
session_manager = None
dispatcher = None


async def run_bot_async():
    global bot_client, session_manager, dispatcher

    init_db()

    bot_client = ClawBotClient()
    session_manager = SessionManager()
    dispatcher = MessageDispatcher(session_manager, bot_client)

    @bot_client.on_qrcode
    async def on_qrcode(qrcode: str, qrcode_img: str):
        logger.info(f"二维码获取成功: {qrcode_img}")
        print(f"\n📱 请使用微信扫描二维码登录:")
        print(f"   {qrcode_img}\n")

    @bot_client.on_login
    async def on_login(credentials):
        logger.info(f"登录成功: bot_id={credentials.ilink_bot_id}")

    @bot_client.on_message
    async def on_message(message: dict):
        await dispatcher.dispatch(message)

    await bot_client.login()
    await bot_client.start_polling()


def run_bot():
    asyncio.run(run_bot_async())


def run_web():
    import uvicorn
    from .web.app import create_app

    init_db()
    app = create_app(bot_client=bot_client)
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
