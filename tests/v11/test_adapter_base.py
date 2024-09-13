from asyncio import Queue, create_task

from melobot.bot import Bot
from melobot.handle import Flow, node
from melobot.log import GenericLogger
from melobot.plugin import Plugin

from melobot_protocol_onebot.v11.adapter.base import Adapter
from melobot_protocol_onebot.v11.adapter.event import MessageEvent
from melobot_protocol_onebot.v11.io.base import BaseIO
from melobot_protocol_onebot.v11.io.packet import EchoPacket, InPacket, OutPacket
from tests.base import *

_TEST_EVENT_DICT = {
    "time": 1725292489,
    "self_id": 123456,
    "post_type": "message",
    "message_type": "group",
    "sub_type": "normal",
    "sender": {
        "age": 0,
        "nickname": "这是一个群昵称",
        "sex": "unknown",
        "user_id": 1574260633,
        "area": "",
        "card": "",
        "level": "",
        "role": "member",
        "title": "",
    },
    "message_id": -1234567890,
    "font": 0,
    "message": "",
    "user_id": 1574260633,
    "anonymous": None,
    "group_id": 535705163,
    "raw_message": "",
}


class TempIO(BaseIO):
    def __init__(self) -> None:
        super().__init__(1)
        self.queue = Queue()
        self.queue.put_nowait(InPacket(data=_TEST_EVENT_DICT))

    async def open(self) -> None:
        pass

    def opened(self) -> bool:
        return True

    async def close(self) -> None:
        pass

    async def input(self) -> InPacket:
        return await self.queue.get()

    async def output(self, packet: OutPacket) -> EchoPacket:
        if packet.echo_id is None:
            return EchoPacket(noecho=True)
        return EchoPacket(
            data={"data": {"message_id": 123456}, "status": "ok", "retcode": 0},
            action_type="send_msg",
        )


@node
async def process(event: MessageEvent, logger: GenericLogger) -> None:
    assert isinstance(event, MessageEvent)
    logger.info("adapter main event process ok")


class TempPlugin(Plugin):
    version = "1.0.0"
    flows = [Flow("test_flow", [process])]


async def after_bot_started(bot: Bot):
    adapter = next(iter(bot.adapters.values()))
    pending = await adapter.with_echo(adapter.send)("Hello World!", user_id=12345)
    data = (await pending[0]).data
    mid = data["message_id"]
    assert mid == 123456
    await bot.close()


async def test_adapter_base():
    mbot = Bot()
    mbot.add_io(TempIO())
    mbot.add_adapter(Adapter())
    mbot.load_plugin(TempPlugin())
    mbot.on_started(after_bot_started)
    create_task(mbot.internal_run())
    await mbot._rip_signal.wait()
