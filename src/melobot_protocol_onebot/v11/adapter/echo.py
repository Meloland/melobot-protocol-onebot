from __future__ import annotations

from typing import Any, Literal, Mapping, cast

from melobot.adapter.model import Echo as RootEcho
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
        self.raw = kv_pairs

        super().__init__(
            protocol=PROTOCOL_IDENTIFIER,
            ok=self._model.status == "ok",
            status=self._model.retcode,
            data=self._model.data,
        )

    @classmethod
    def resolve(cls, **kwds: Any) -> Echo:
        action_type = kwds.pop("action_type")
        match action_type:
            case "send_private_msg" | "send_group_msg" | "send_msg":
                return SendMsgEcho(**kwds)
            case "send_private_forward_msg" | "send_group_forward_msg":
                return SendForwardMsgEcho(**kwds)
            case "get_msg":
                return GetMsgEcho(**kwds)
            case "get_forward_msg":
                return GetForwardMsgEcho(**kwds)
            case "get_login_info":
                return GetLoginInfoEcho(**kwds)
            case "get_stranger_info":
                return GetStrangerInfoEcho(**kwds)
            case "get_friend_list":
                return GetFriendListEcho(**kwds)
            case "get_group_info":
                return GetGroupInfoEcho(**kwds)
            case "get_group_list":
                return GetGroupListEcho(**kwds)
            case "get_group_member_info":
                return GetGroupMemberInfoEcho(**kwds)
            case "get_group_member_list":
                return GetGroupMemberListEcho(**kwds)
            case "get_group_honor_info":
                return GetGroupHonorInfoEcho(**kwds)
            case "get_cookies":
                return GetCookiesEcho(**kwds)
            case "get_csrf_token":
                return GetCsrfTokenEcho(**kwds)
            case "get_credentials":
                return GetCredentialsEcho(**kwds)
            case "get_record":
                return GetRecordEcho(**kwds)
            case "get_image":
                return GetImageEcho(**kwds)
            case "can_send_image":
                return CanSendImageEcho(**kwds)
            case "can_send_record":
                return CanSendRecordEcho(**kwds)
            case "get_status":
                return GetStatusEcho(**kwds)
            case "get_version_info":
                return GetVersionInfoEcho(**kwds)
            case (
                "delete_msg"
                | "send_like"
                | "set_group_kick"
                | "set_group_ban"
                | "set_group_anonymous_ban"
                | "set_group_whole_ban"
                | "set_group_admin"
                | "set_group_anonymous"
                | "set_group_card"
                | "set_group_name"
                | "set_group_leave"
                | "set_group_special_title"
                | "set_friend_add_request"
                | "set_group_add_request"
                | "set_restart"
                | "clean_cache"
            ):
                return EmptyEcho(**kwds)
            case _:
                return Echo(**kwds)


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


class _GetVersionInfoEchoData(TypedDict):
    app_name: str
    app_version: str
    protocol_version: str


class GetVersionInfoEcho(Echo):

    class Model(Echo.Model):
        data: _GetVersionInfoEchoData

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__(**kv_pairs)

        self._model: GetVersionInfoEcho.Model
        for k, v in kv_pairs["data"].items():
            if k not in self._model.data:
                self.data[k] = v  # type: ignore[literal-required]

    data: _GetVersionInfoEchoData
