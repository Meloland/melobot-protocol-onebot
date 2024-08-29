from typing import Any, Literal

from melobot.adapter.model import Event
from melobot.utils import get_id
from pydantic import BaseModel

from ... import PROTOCOL_IDENTIFIER


class OneBotV11Event(Event):
    class Model(BaseModel):
        time: int
        self_id: int
        post_type: Literal["message", "notice", "request", "meta_event"]
        format: Literal["array", "string"]

    def __init__(self, **kv_pairs: dict[str, Any]) -> None:
        self._model = OneBotV11Event.Model(**kv_pairs)
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

    @property
    def format(self) -> Literal["array", "string"]:
        return self._model.format
