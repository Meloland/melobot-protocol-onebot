from typing import Any, Literal

from melobot.adapter.model import Event as RootEvent
from melobot.utils import get_id
from pydantic import BaseModel

from ..const import PROTOCOL_IDENTIFIER


class Event(RootEvent):
    class Model(BaseModel):
        time: int
        self_id: int
        post_type: Literal["message", "notice", "request", "meta_event"]

    def __init__(self, **kv_pairs: Any) -> None:
        self._model = self.Model(**kv_pairs)
        self.time: int

        super().__init__(
            self._model.time, get_id(), PROTOCOL_IDENTIFIER, scope=(), contents=()
        )

    @property
    def self_id(self) -> int:
        return self._model.self_id

    @property
    def post_type(self) -> Literal["message", "notice", "request", "meta_event"]:
        return self._model.post_type


class MessageEvent(Event):
    class Model(Event.Model):
        message_type: Literal["private", "group"]
        sub_type: Literal["friend", "group", "other", "normal", "anonymous", "notice"]
        message_id: int
        user_id: int
