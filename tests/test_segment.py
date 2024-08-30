from typing import Literal

from typing_extensions import TypedDict

from melobot_protocol_onebot.v11.adapter import msg
from tests.base import *


async def test_image_seg():
    MySegment = msg.Segment.new_type(Literal["my"], TypedDict("MyData", {"key": str}))
    s = MySegment(key="123")
    print(s.type, s.data)
    print(msg.Segment.__subclasses__())
    assert s.type == "my"
    assert s.data["key"] == "123456"
