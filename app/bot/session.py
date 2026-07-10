import threading
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class UserSession:
    wechat_id: str
    state: str = "auth_select"
    user_db_id: Optional[int] = None
    page: int = 1
    selected_product_id: Optional[int] = None
    temp_data: dict = field(default_factory=dict)

    def reset(self):
        self.state = "auth_select"
        self.user_db_id = None
        self.page = 1
        self.selected_product_id = None
        self.temp_data = {}

    def go_home(self):
        if self.user_db_id:
            self.state = "home"
        else:
            self.state = "auth_select"
        self.page = 1
        self.selected_product_id = None
        self.temp_data = {}


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, UserSession] = {}
        self._lock = threading.Lock()

    def get(self, wechat_id: str) -> UserSession:
        with self._lock:
            if wechat_id not in self._sessions:
                self._sessions[wechat_id] = UserSession(wechat_id=wechat_id)
            return self._sessions[wechat_id]

    def set(self, wechat_id: str, session: UserSession):
        with self._lock:
            self._sessions[wechat_id] = session

    def remove(self, wechat_id: str):
        with self._lock:
            self._sessions.pop(wechat_id, None)

    def clear_all(self):
        with self._lock:
            self._sessions.clear()
