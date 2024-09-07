from time import time_ns
from typing import Any, Literal, Mapping, cast

from melobot.adapter.model import Echo as RootEcho
from melobot.utils import get_id
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..const import PROTOCOL_IDENTIFIER
from .event import _GroupMessageSender, _MessageSender
from .segment import NodeSegment, Segment


class Echo(RootEcho):

    class Model(BaseModel):
        status: Literal["ok", "async", "failed"]
        retcode: int
        data: Mapping[str, Any] | list | None

    def __init__(self, **kv_pairs: Any) -> None:
        self._model = self.Model(**kv_pairs)
        self.raw_data = kv_pairs

        super().__init__(
            int(time_ns() / 1e9),
            get_id(),
            PROTOCOL_IDENTIFIER,
            scope=(),
            ok=self._model.status == "ok",
            status=self._model.retcode,
            data=self._model.data,
        )


class EmptyEcho(Echo):

    class Model(Echo.Model):
        data: None

    data: None


class _SendMsgEchoData(TypedDict):
    message_id: int


class SendMsgEcho(Echo):

    class Model(Echo.Model):
        data: _SendMsgEchoData

    data: _SendMsgEchoData


class _SendForwardMsgEchoData(TypedDict):
    message_id: int
    forward_id: str


class SendForwardMsgEcho(Echo):

    class Model(Echo.Model):
        data: _SendForwardMsgEchoData

    data: _SendForwardMsgEchoData


class _GetMsgEchoData(TypedDict):
    time: int
    message_type: Literal["private", "group"]
    message_id: int
    real_id: int


class _GetMsgEchoDataInterface(_GetMsgEchoData):
    sender: _MessageSender | _GroupMessageSender
    message: list[Segment]


class GetMsgEcho(Echo):

    class Model(Echo.Model):
        data: _GetMsgEchoData

    data: _GetMsgEchoDataInterface

    def __init__(self, **kv_pairs: Any) -> None:
        data = kv_pairs["data"]
        msgs = data["message"]
        segs: list[Segment]
        if isinstance(msgs, str):
            segs = Segment.resolve_cq(msgs)
        else:
            segs = [Segment.resolve(seg_dic["type"], seg_dic["data"]) for seg_dic in msgs]

        sender: _MessageSender | _GroupMessageSender
        if data["message_type"] == "private":
            sender = _MessageSender(**data["sender"])
        else:
            sender = _GroupMessageSender(**data["sender"])

        super().__init__(**kv_pairs)
        self.data["message"] = segs
        self.data["sender"] = sender


class _GetForwardMsgEchoData(TypedDict): ...


class _GetForwardMsgEchoDataInterface(_GetForwardMsgEchoData):
    message: list[NodeSegment]


class GetForwardMsgEcho(Echo):

    class Model(Echo.Model):
        data: _GetForwardMsgEchoData

    data: _GetForwardMsgEchoDataInterface

    def __init__(self, **kv_pairs: Any) -> None:
        data = kv_pairs["data"]
        msgs = data["message"]
        segs: list[Segment]
        if isinstance(msgs, str):
            segs = Segment.resolve_cq(msgs)
        else:
            segs = [Segment.resolve(seg_dic["type"], seg_dic["data"]) for seg_dic in msgs]

        super().__init__(**kv_pairs)
        self.data["message"] = cast(list[NodeSegment], segs)


class _GetLoginInfoEchoData(TypedDict):
    user_id: int
    nickname: str


class GetLoginInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetLoginInfoEchoData

    data: _GetLoginInfoEchoData


class _GetStrangerInfoEchoData(TypedDict):
    user_id: int
    nickname: str
    sex: Literal["male", "female", "unknown"]
    age: int


class GetStrangerInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetStrangerInfoEchoData

    data: _GetStrangerInfoEchoData


class _GetFriendListEchoElem(TypedDict):
    user_id: int
    nickname: str
    remark: str


class GetFriendListEcho(Echo):

    class Model(Echo.Model):
        data: list[_GetFriendListEchoElem]

    data: list[_GetFriendListEchoElem]


class _GetGroupInfoEchoData(TypedDict):
    group_id: int
    group_name: str
    member_count: int
    max_member_count: int


class GetGroupInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetGroupInfoEchoData

    data: _GetGroupInfoEchoData


class GetGroupListEcho(Echo):

    class Model(Echo.Model):
        data: list[_GetGroupInfoEchoData]

    data: list[_GetGroupInfoEchoData]


class _GetGroupMemberInfoEchoData(TypedDict):
    group_id: int
    user_id: int
    nickname: str
    card: str
    sex: str
    age: int
    area: str
    join_time: int
    last_sent_time: int
    level: str
    role: Literal["owner", "admin", "member"]
    unfriendly: bool
    title: str
    title_expire_time: int
    card_changeable: bool


class GetGroupMemberInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetGroupMemberInfoEchoData

    data: _GetGroupMemberInfoEchoData


class GetGroupMemberListEcho(Echo):

    class Model(Echo.Model):
        data: list[_GetGroupMemberInfoEchoData]

    data: list[_GetGroupMemberInfoEchoData]


class _CurrentTalkativeData(TypedDict):
    user_id: int
    nickname: str
    avatar: str
    day_count: int


class _OtherListData(TypedDict):
    user_id: int
    nickname: str
    avatar: str
    description: str


class _GetGroupHonorInfoEchoData(TypedDict):
    group_id: int
    current_talkative: _CurrentTalkativeData | None
    talkative_list: list[_OtherListData] | None
    performer_list: list[_OtherListData] | None
    legend_list: list[_OtherListData] | None
    strong_newbie_list: list[_OtherListData] | None
    emotion_list: list[_OtherListData] | None


class GetGroupHonorInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetGroupHonorInfoEchoData

    data: _GetGroupHonorInfoEchoData


class _GetCookiesEchoData(TypedDict):
    cookies: str


class GetCookiesEcho(Echo):

    class Model(Echo.Model):
        data: _GetCookiesEchoData

    data: _GetCookiesEchoData


class _GetCsrfTokenEchoData(TypedDict):
    token: int


class GetCsrfTokenEcho(Echo):

    class Model(Echo.Model):
        data: _GetCsrfTokenEchoData

    data: _GetCsrfTokenEchoData


class _GetCredentialsEchoData(TypedDict):
    cookies: str
    csrf_token: int


class GetCredentialsEcho(Echo):

    class Model(Echo.Model):
        data: _GetCredentialsEchoData

    data: _GetCredentialsEchoData


class _GetRecordEchoData(TypedDict):
    file: str


class GetRecordEcho(Echo):

    class Model(Echo.Model):
        data: _GetRecordEchoData

    data: _GetRecordEchoData


class _GetImageEchoData(TypedDict):
    file: str


class GetImageEcho(Echo):

    class Model(Echo.Model):
        data: _GetImageEchoData

    data: _GetImageEchoData


class _CanSendImageEchoData(TypedDict):
    yes: bool


class CanSendImageEcho(Echo):

    class Model(Echo.Model):
        data: _CanSendImageEchoData

    data: _CanSendImageEchoData


class _CanSendRecordEchoData(TypedDict):
    yes: bool


class CanSendRecordEcho(Echo):

    class Model(Echo.Model):
        data: _CanSendRecordEchoData

    data: _CanSendRecordEchoData


class _GetStatusEchoData(TypedDict):
    online: bool
    good: bool


class GetStatusEcho(Echo):

    class Model(Echo.Model):
        data: _GetStatusEchoData

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__(**kv_pairs)

        self._model: GetStatusEcho.Model
        for k, v in kv_pairs["data"].items():
            if k not in self._model.data:
                self.data[k] = v  # type: ignore[literal-required]

    data: _GetStatusEchoData


class _GetVersionEchoData(TypedDict):
    app_name: str
    app_version: str
    protocol_version: str


class GetVersionEcho(Echo):

    class Model(Echo.Model):
        data: _GetVersionEchoData

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__(**kv_pairs)

        self._model: GetVersionEcho.Model
        for k, v in kv_pairs["data"].items():
            if k not in self._model.data:
                self.data[k] = v  # type: ignore[literal-required]

    data: _GetVersionEchoData
