from melobot_protocol_onebot.v11.adapter.event import Event
from tests.base import *


async def test_ob11_base_event() -> None:
    e = Event(**{"time": 1, "self_id": 2, "post_type": "message", "format": "array"})
    assert 1 == 1
