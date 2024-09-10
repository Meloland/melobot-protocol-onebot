from melobot.io import EchoPacket as RootEchoPak
from melobot.io import InPacket as RootInPack
from melobot.io import OutPacket as RootOutPak

from ..const import PROTOCOL_IDENTIFIER


class InPacket(RootInPack):
    protocol: str = PROTOCOL_IDENTIFIER
    data: dict


class OutPacket(RootOutPak):
    protocol: str = PROTOCOL_IDENTIFIER
    action_type: str
    action_params: dict
    echo_id: str | None
    data: str


class EchoPacket(RootEchoPak):
    protocol: str = PROTOCOL_IDENTIFIER
    echo_id: str | None
    data: dict
