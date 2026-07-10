import httpx
import base64
import random
import json
import logging
from typing import Optional, Callable, Awaitable
from ..config import CLAWBOT_BASE_URL, BOT_TYPE

logger = logging.getLogger(__name__)


class ClawBotCredentials:
    def __init__(self, bot_token: str = "", ilink_bot_id: str = "",
                 ilink_user_id: str = "", baseurl: str = ""):
        self.bot_token = bot_token
        self.ilink_bot_id = ilink_bot_id
        self.ilink_user_id = ilink_user_id
        self.baseurl = baseurl or CLAWBOT_BASE_URL


class ClawBotClient:
    def __init__(self, base_url: str = CLAWBOT_BASE_URL, bot_type: int = BOT_TYPE):
        self.base_url = base_url
        self.bot_type = bot_type
        self.credentials: Optional[ClawBotCredentials] = None
        self._client = httpx.AsyncClient(timeout=30.0)
        self._uin = self._generate_uin()
        self._on_qrcode_callback: Optional[Callable[[str, str], Awaitable[None]]] = None
        self._on_login_callback: Optional[Callable[[ClawBotCredentials], Awaitable[None]]] = None
        self._on_message_callback: Optional[Callable[[dict], Awaitable[None]]] = None

    @staticmethod
    def _generate_uin() -> str:
        uin = random.randint(100000000, 999999999)
        return base64.b64encode(str(uin).encode()).decode()

    def _get_headers(self, auth: bool = False) -> dict:
        headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "iLink-App-Id": "bot",
            "iLink-App-ClientVersion": "132102",
            "X-WECHAT-UIN": self._uin,
        }
        if auth and self.credentials and self.credentials.bot_token:
            headers["Authorization"] = f"Bearer {self.credentials.bot_token}"
        return headers

    def on_qrcode(self, callback: Callable[[str, str], Awaitable[None]]):
        self._on_qrcode_callback = callback
        return callback

    def on_login(self, callback: Callable[[ClawBotCredentials], Awaitable[None]]):
        self._on_login_callback = callback
        return callback

    def on_message(self, callback: Callable[[dict], Awaitable[None]]):
        self._on_message_callback = callback
        return callback

    async def get_qrcode(self) -> tuple[str, str]:
        url = f"{self.base_url}/ilink/bot/get_bot_qrcode?bot_type={self.bot_type}"
        try:
            resp = await self._client.post(url, json={"local_token_list": []}, headers=self._get_headers())
            data = resp.json()
            if data.get("ret") == 0:
                qrcode = data["qrcode"]
                qrcode_img = data["qrcode_img_content"]
                logger.info(f"获取二维码成功: {qrcode}")
                if self._on_qrcode_callback:
                    await self._on_qrcode_callback(qrcode, qrcode_img)
                return qrcode, qrcode_img
            else:
                logger.error(f"获取二维码失败: {data}")
                raise RuntimeError(f"获取二维码失败: {data}")
        except Exception as e:
            logger.error(f"获取二维码异常: {e}")
            raise

    async def check_qrcode_status(self, qrcode: str) -> dict:
        url = f"{self.base_url}/ilink/bot/get_qrcode_status?qrcode={qrcode}"
        try:
            resp = await self._client.get(url, headers=self._get_headers())
            data = resp.json()
            logger.debug(f"二维码状态: {data}")
            return data
        except Exception as e:
            logger.error(f"查询二维码状态异常: {e}")
            raise

    async def login(self) -> ClawBotCredentials:
        qrcode, qrcode_img = await self.get_qrcode()

        import asyncio
        while True:
            await asyncio.sleep(3)
            try:
                status_data = await self.check_qrcode_status(qrcode)
                status = status_data.get("status", "wait")

                if status == "confirmed":
                    credentials = ClawBotCredentials(
                        bot_token=status_data.get("bot_token", ""),
                        ilink_bot_id=status_data.get("ilink_bot_id", ""),
                        ilink_user_id=status_data.get("ilink_user_id", ""),
                        baseurl=status_data.get("baseurl", self.base_url),
                    )
                    self.credentials = credentials
                    logger.info("登录成功")
                    if self._on_login_callback:
                        await self._on_login_callback(credentials)
                    return credentials
                elif status == "expired":
                    logger.info("二维码已过期，重新获取")
                    qrcode, qrcode_img = await self.get_qrcode()
                elif status == "scaned":
                    logger.debug("已扫码，等待确认")
                else:
                    logger.debug("等待扫码")
            except Exception as e:
                logger.error(f"轮询二维码状态异常: {e}")
                await asyncio.sleep(5)

    async def send_message(self, to_user: str, content: str) -> bool:
        if not self.credentials:
            logger.error("未登录，无法发送消息")
            return False

        url = f"{self.credentials.baseurl}/ilink/bot/send_message"
        try:
            payload = {
                "to_user": to_user,
                "content": content,
                "msg_type": 1,
            }
            resp = await self._client.post(
                url,
                json=payload,
                headers=self._get_headers(auth=True),
            )
            data = resp.json()
            if data.get("ret") == 0:
                logger.info(f"消息发送成功: {to_user}")
                return True
            else:
                logger.error(f"消息发送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False

    async def get_updates(self, sync_key: str = "") -> tuple[list[dict], str]:
        if not self.credentials:
            logger.error("未登录，无法获取消息")
            return [], sync_key

        url = f"{self.credentials.baseurl}/ilink/bot/getupdates"
        try:
            payload = {
                "get_updates_buf": sync_key,
                "base_info": {
                    "bot_type": self.bot_type,
                    "ilink_bot_id": self.credentials.ilink_bot_id,
                },
            }
            resp = await self._client.post(
                url,
                json=payload,
                headers=self._get_headers(auth=True),
            )
            data = resp.json()
            if data.get("ret") == 0:
                messages = data.get("msgs", [])
                new_sync_key = data.get("get_updates_buf", sync_key)
                return messages, new_sync_key
            else:
                logger.error(f"获取消息失败: {data}")
                return [], sync_key
        except Exception as e:
            logger.error(f"获取消息异常: {e}")
            return [], sync_key

    async def start_polling(self):
        import asyncio
        sync_key = ""
        logger.info("开始消息轮询")
        while True:
            try:
                messages, sync_key = await self.get_updates(sync_key)
                for msg in messages:
                    if self._on_message_callback:
                        await self._on_message_callback(msg)
                if not messages:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"消息轮询异常: {e}")
                await asyncio.sleep(5)

    async def close(self):
        await self._client.aclose()
