import json
from time import time_ns
from typing import Any, Iterable, Optional

from melobot.adapter.model import Action as RootAction
from melobot.handle import try_get_event
from melobot.utils import get_id

from ..const import PROTOCOL_IDENTIFIER
from .segment import NodeSegment, Segment


class Action(RootAction):
    def __init__(self, type: str, params: dict[str, Any]) -> None:
        self.time: int

        super().__init__(
            int(time_ns() / 1e9),
            get_id(),
            PROTOCOL_IDENTIFIER,
            scope=(),
            contents=(),
            trigger=try_get_event(),
        )

        self.type = type
        self.params = params
        self.need_echo = False

    def set_echo(self, status: bool) -> None:
        self.need_echo = status

    def extract(self) -> dict[str, Any]:
        obj = {
            "action": self.type,
            "params": self.params,
        }
        if self.need_echo:
            obj["echo"] = self.id
        return obj

    def flatten(self) -> str:
        return json.dumps(self.extract(), ensure_ascii=False)


class MessageAction(Action):
    def __init__(
        self,
        msgs: Iterable[Segment],
        is_private: bool,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
    ) -> None:
        type = "send_msg"
        _msgs = list(msgs)
        if is_private:
            params = {
                "message_type": "private",
                "user_id": user_id,
                "message": _msgs,
                "auto_escape": False,
            }
        else:
            params = {
                "message_type": "group",
                "group_id": group_id,
                "message": _msgs,
                "auto_escape": False,
            }
        super().__init__(type, params)


class ForwardMessageAction(Action):
    def __init__(
        self,
        msgs: Iterable[NodeSegment],
        is_private: bool,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
    ) -> None:
        _msgs = list(msgs)
        if is_private:
            type = "send_private_forward_msg"
            params = {"user_id": user_id, "messages": _msgs, "auto_escape": False}
        else:
            type = "send_group_forward_msg"
            params = {"group_id": group_id, "messages": _msgs, "auto_escape": False}
        super().__init__(type, params)
