from __future__ import annotations

from typing import Any, Literal

from melobot.adapter.model import Event as RootEvent
from melobot.utils import get_id
from pydantic import BaseModel

from ..const import PROTOCOL_IDENTIFIER
from .msg import Segment


class Event(RootEvent):
    class Model(BaseModel):
        time: int
        self_id: int
        post_type: Literal["message", "notice", "request", "meta_event"]

    def __init__(self, **event_data: Any) -> None:
        self._model = self.Model(**event_data)
        self.time: int

        super().__init__(
            self._model.time, get_id(), PROTOCOL_IDENTIFIER, scope=(), contents=()
        )

    @classmethod
    def resolve(cls, event_data: dict[str, Any]) -> Event:
        cls_map: dict[str, type[Event]] = {
            "message": MessageEvent,
            "notice": NoticeEvent,
            "request": RequestEvent,
            "meta_event": MetaEvent,
        }
        return cls_map[event_data["post_type"]].resolve(event_data)

    @property
    def self_id(self) -> int:
        return self._model.self_id

    @property
    def post_type(self) -> Literal["message", "notice", "request", "meta_event"]:
        return self._model.post_type


class _MessageSender(BaseModel):
    user_id: int | None = None
    nickname: str | None = None
    sex: Literal["male", "female", "unknown"] | None = None
    age: int | None = None


class MessageEvent(Event):
    class Model(Event.Model):
        message_type: Literal["private", "group"]
        sub_type: Literal["friend", "group", "other", "normal", "anonymous", "notice"]
        message_id: int
        user_id: int
        message: list[Segment.Model]
        raw_message: str
        font: int
        sender: _MessageSender

    def __init__(self, **event_data: Any) -> None:
        super().__init__(**event_data)


class MetaEvent(Event): ...


class NoticeEvent(Event): ...


class RequestEvent(Event): ...
