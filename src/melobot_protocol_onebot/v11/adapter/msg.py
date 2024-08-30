from __future__ import annotations

import re
from functools import partial
from itertools import chain, zip_longest
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Match,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    overload,
)

from beartype.door import is_subhint
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, UrlConstraints, create_model
from typing_extensions import NotRequired, Self, TypedDict

from ..const import T, V

FileUrl: TypeAlias = Annotated[
    AnyUrl, UrlConstraints(allowed_schemes=["http", "https", "file", "base64"])
]


class _BaseTypedDict(TypedDict): ...


_SegTypeT = TypeVar("_SegTypeT", bound=str)
_SegDataT = TypeVar("_SegDataT", bound=_BaseTypedDict)


def cq_filter_text(s: str) -> str:
    """cq 文本过滤函数

    可从 cq 字符串中过滤出纯文本消息部分

    :param s: cq 字符串
    :return: 纯文本消息部分
    """
    regex = re.compile(r"\[CQ:.*?\]")
    return regex.sub("", s)


def cq_escape(text: str) -> str:
    """cq 字符串特殊符号转义

    如：将 "&" 转义为 "&amp;"

    :param text: 需要转义的 cq 字符串
    :return: 转义特殊符号后的 cq 字符串
    """
    return (
        text.replace("&", "&amp;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace(",", "&#44;")
    )


def cq_anti_escape(text: str) -> str:
    """cq 字符串特殊符号逆转义

    如：将 "&amp;" 逆转义为 "&"

    :param text: 需要逆转义的 cq 字符串
    :return: 逆转义特殊符号后的 cq 字符串
    """
    return (
        text.replace("&#44;", ",")
        .replace("&#93;", "]")
        .replace("&#91;", "[")
        .replace("&amp;", "&")
    )


# def cq_to_segments(s: str) -> list[Segment]:
#     """将 cq 字符串转换为消息段对象列表

#     :param s: cq 字符串
#     :return: 消息段对象列表
#     """

#     cq_texts: list[str] = []

#     def replace_func(m: Match) -> str:
#         s, e = m.regs[0]
#         cq_texts.append(m.string[s:e])
#         return "\u0000"

#     cq_regex = re.compile(r"\[CQ:.*?\]")

#     no_cq_str = cq_regex.sub(replace_func, s)
#     pure_texts = map(
#         lambda x: f"[CQ:text,text={x}]" if x != "" else x,
#         no_cq_str.split("\u0000"),
#     )
#     cq_entity_str: str = "".join(
#         chain.from_iterable(zip_longest(pure_texts, cq_texts, fillvalue=""))
#     )

#     cq_entity: list[str] = cq_entity_str.split("]")[:-1]
#     segs: list[Segment] = []

#     for e in cq_entity:
#         cq_parts = e.split(",")
#         cq_type = cq_parts[0][4:]
#         data: dict[str, float | int | str] = {}

#         for param_pair in cq_parts[1:]:
#             name, val = param_pair.split("=")

#             if cq_type != "text":
#                 val = cq_anti_escape(val)

#             try:
#                 data[name] = float(val)
#                 tmp = int(val)
#                 if tmp == data[name]:
#                     data[name] = tmp
#             except Exception:
#                 data[name] = val

#         segs.append({"type": cq_type, "data": data})

#     return segs


class Segment(Generic[_SegTypeT, _SegDataT]):

    class Model(BaseModel):
        type: str
        data: dict

    def __init__(self, seg_type: _SegTypeT, seg_data: _SegDataT) -> None:
        self._model = self.Model(
            type=seg_type, data={k: v for k, v in seg_data.items() if v is not None}
        )

    @staticmethod
    def new_type(
        seg_type_hint: type[T],
        seg_data_hint: type[V],
    ) -> type[_CustomSegInterface[T, V]]:  # type: ignore[type-var]
        if not is_subhint(seg_type_hint, Literal):
            raise ValueError("新消息段的类型标注必须为 Literal")
        if not is_subhint(seg_data_hint, TypedDict):
            raise ValueError("新消息段的类型标注必须为 TypedDict")
        hint_args = get_args(seg_type_hint)
        if len(hint_args) != 1:
            raise ValueError("新消息段的类型标注必须只有一个字面量")
        type_v: str = hint_args[0]

        seg_cls = _CustomSegmentMeta(
            f"Dynamic_{type_v.capitalize()}_Segment",
            (Segment,),
            {
                "Model": create_model(
                    f"_Dynamic_{type_v.capitalize()}_SegmentData",
                    type=(seg_type_hint, ...),
                    data=(seg_data_hint, ...),
                ),
                "SegTypeVal": type_v,
            },
        )
        setattr(
            seg_cls,
            "__init__",
            partial(_CustomSegmentMeta.__custom_seg_cls_init__, seg_cls),
        )
        return cast(type[_CustomSegInterface[T, V]], seg_cls)  # type: ignore[type-var]

    @property
    def type(self) -> _SegTypeT:
        return cast(_SegTypeT, self._model.type)

    @property
    def data(self) -> _SegDataT:
        return cast(_SegDataT, self._model.data)

    @property
    def cq_str(self) -> str:
        if self._model.type == "text":
            return cast(_TextData, self._model.data)["text"]

        params = ",".join(f"{k}={cq_escape(str(v))}" for k, v in self._model.data.items())
        s = f"[CQ:{self._model.type}]"
        if params != "":
            s += f",{params}"
        return s


class _CustomSegmentMeta(type):
    def __init__(cls, name: str, bases: tuple[type], attrs: dict[str, Any]) -> None:
        super().__init__(name, bases, attrs)

    @staticmethod
    def __custom_seg_cls_init__(  # pylint: disable=bad-staticmethod-argument
        self: type, **data: Any
    ) -> None:
        self._model = getattr(self, "Model")(  # type: ignore[attr-defined]
            type=getattr(self, "SegTypeVal"),
            data=data,
        )


class _CustomSegInterface(Segment[_SegTypeT, _SegDataT]):
    def __init__(  # pylint: disable=super-init-not-called,unused-argument
        self, **data: Any
    ) -> None: ...


class _TextData(TypedDict):
    text: str


class TextSegment(Segment[Literal["text"], _TextData]):

    class Model(BaseModel):
        type: Literal["text"]
        data: _TextData

    def __init__(self, text: str) -> None:
        super().__init__("text", _TextData(text=text))


class _FaceData(TypedDict):
    id: int


class FaceSegment(Segment[Literal["face"], _FaceData]):

    class Model(BaseModel):
        type: Literal["face"]
        data: _FaceData

    def __init__(self, id: int) -> None:
        super().__init__("face", _FaceData(id=id))


class _ImageSendData(TypedDict):
    file: str | FileUrl
    type: NotRequired[Literal["flash"]]
    cache: NotRequired[Literal[0, 1]]
    proxy: NotRequired[Literal[0, 1]]
    timeout: NotRequired[int]


class _ImageRecvData(TypedDict):
    file: str
    type: NotRequired[Literal["flash"]]
    url: FileUrl


class ImageSegment(Segment[Literal["image"], _ImageSendData | _ImageRecvData]):

    class Model(BaseModel):
        type: Literal["image"]
        data: _ImageSendData | _ImageRecvData

    @overload
    def __init__(
        self,
        *,
        file: str | FileUrl,
        type: Literal["flash"] | None = None,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self, *, file: str, url: FileUrl, type: Literal["flash"] | None = None
    ) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__("image", cast(_ImageSendData | _ImageRecvData, kv_pairs))


class ImageSendSegment(ImageSegment):
    def __init__(
        self,
        *,
        file: str | FileUrl,
        type: Literal["flash"] | None = None,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None = None,
    ) -> None:
        super().__init__(file=file, type=type, cache=cache, proxy=proxy, timeout=timeout)

    data: _ImageSendData


class ImageRecvSegment(ImageSegment):
    def __init__(
        self, *, file: str, url: FileUrl, type: Literal["flash"] | None = None
    ) -> None:
        super().__init__(file=file, url=url, type=type)

    data: _ImageRecvData


class _RecordSendData(TypedDict):
    file: str | FileUrl
    magic: NotRequired[Literal[0, 1]]
    cache: NotRequired[Literal[0, 1]]
    proxy: NotRequired[Literal[0, 1]]
    timeout: NotRequired[int]


class _RecordRecvData(TypedDict):
    file: str
    magic: NotRequired[Literal[0, 1]]
    url: FileUrl


class RecordSegment(Segment[Literal["record"], _RecordSendData | _RecordRecvData]):

    class Model(BaseModel):
        type: Literal["record"]
        data: _RecordSendData | _RecordRecvData

    @overload
    def __init__(
        self,
        *,
        file: str | FileUrl,
        magic: Literal[0, 1] | None = None,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None,
    ) -> None: ...

    @overload
    def __init__(
        self, *, file: str, url: FileUrl, magic: Literal[0, 1] | None = None
    ) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__("record", cast(_RecordSendData | _RecordRecvData, kv_pairs))


class RecordSendSegment(RecordSegment):
    def __init__(
        self,
        *,
        file: str | FileUrl,
        magic: Literal[0, 1] | None = None,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None,
    ) -> None:
        super().__init__(
            file=file, magic=magic, cache=cache, proxy=proxy, timeout=timeout
        )

    data: _RecordSendData


class RecordRecvSegment(RecordSegment):
    def __init__(
        self, *, file: str, url: FileUrl, magic: Literal[0, 1] | None = None
    ) -> None:
        super().__init__(file=file, url=url, magic=magic)

    data: _RecordRecvData


class _VideoSendData(TypedDict):
    file: str | FileUrl
    cache: NotRequired[Literal[0, 1]]
    proxy: NotRequired[Literal[0, 1]]
    timeout: NotRequired[int]


class _VideoRecvData(TypedDict):
    file: str
    url: FileUrl


class VideoSegment(Segment[Literal["video"], _VideoSendData | _VideoRecvData]):

    class Model(BaseModel):
        type: Literal["video"]
        data: _VideoSendData | _VideoRecvData

    @overload
    def __init__(
        self,
        *,
        file: str | FileUrl,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None,
    ) -> None: ...

    @overload
    def __init__(self, *, file: str, url: FileUrl) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__("video", cast(_VideoSendData | _VideoRecvData, kv_pairs))


class VideoSendSegment(VideoSegment):
    def __init__(
        self,
        *,
        file: str | FileUrl,
        cache: Literal[0, 1] | None = None,
        proxy: Literal[0, 1] | None = None,
        timeout: int | None,
    ) -> None:
        super().__init__(file=file, cache=cache, proxy=proxy, timeout=timeout)

    data: _VideoSendData


class VideoRecvSegment(VideoSegment):
    def __init__(self, *, file: str, url: FileUrl) -> None:
        super().__init__(file=file, url=url)

    data: _VideoRecvData


class _AtData(TypedDict):
    qq: int | Literal["all"]


class AtSegment(Segment[Literal["at"], _AtData]):

    class Model(BaseModel):
        type: Literal["at"]
        data: _AtData

    def __init__(self, qq: int | Literal["all"]) -> None:
        super().__init__("at", _AtData(qq=qq))


class _RpsData(TypedDict): ...


class RpsSegment(Segment[Literal["rps"], _RpsData]):

    class Model(BaseModel):
        type: Literal["rps"]
        data: _RpsData

    def __init__(self) -> None:
        super().__init__("rps", _RpsData())


class _DictData(TypedDict): ...


class DiceSegment(Segment[Literal["dice"], _DictData]):

    class Model(BaseModel):
        type: Literal["dice"]
        data: _DictData

    def __init__(self) -> None:
        super().__init__("dice", _DictData())


class _ShakeData(TypedDict): ...


class ShakeSegment(Segment[Literal["shake"], _ShakeData]):

    class Model(BaseModel):
        type: Literal["shake"]
        data: _ShakeData

    def __init__(self) -> None:
        super().__init__("shake", _ShakeData())


class _PokeSendData(TypedDict):
    type: str
    id: int


class _PokeRecvData(TypedDict):
    type: str
    id: int
    name: int


class PokeSegment(Segment[Literal["poke"], _PokeSendData | _PokeRecvData]):

    class Model(BaseModel):
        type: Literal["poke"]
        data: _PokeSendData | _PokeRecvData

    @overload
    def __init__(self, *, type: str, id: int) -> None: ...

    @overload
    def __init__(self, *, type: str, id: int, name: int) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__("poke", cast(_PokeSendData | _PokeRecvData, kv_pairs))


class PokeSendSegment(PokeSegment):
    def __init__(self, type: str, id: int) -> None:
        super().__init__(type=type, id=id)

    data: _PokeSendData


class PokeRecvSegment(PokeSegment):
    def __init__(self, type: str, id: int, name: int) -> None:
        super().__init__(type=type, id=id, name=name)

    data: _PokeRecvData


class _AnonymousData(TypedDict):
    ignore: NotRequired[Literal[0, 1]]


class AnonymousSegment(Segment[Literal["anonymous"], _AnonymousData]):

    class Model(BaseModel):
        type: Literal["anonymous"]
        data: _AnonymousData

    def __init__(self, ignore: Literal[0, 1] | None = None) -> None:
        super().__init__("anonymous", cast(_AnonymousData, {"ignore": ignore}))


class _ShareData(TypedDict):
    url: AnyUrl
    title: str
    content: str
    image: AnyHttpUrl


class ShareSegment(Segment[Literal["share"], _ShareData]):

    class Model(BaseModel):
        type: Literal["share"]
        data: _ShareData

    def __init__(self, url: AnyUrl, title: str, content: str, image: AnyHttpUrl) -> None:
        super().__init__(
            "share", _ShareData(url=url, title=title, content=content, image=image)
        )


class _ContactFriendData(TypedDict):
    type: Literal["qq"]
    id: int


class _ContactGroupData(TypedDict):
    type: Literal["group"]
    id: int


class ContactSegment(Segment[Literal["contact"], _ContactFriendData | _ContactGroupData]):

    class Model(BaseModel):
        type: Literal["contact"]
        data: _ContactFriendData | _ContactGroupData

    def __init__(self, type: Literal["qq", "group"], id: int) -> None:
        super().__init__(
            "contact",
            cast(_ContactFriendData | _ContactGroupData, {"type": type, "id": id}),
        )


class ContactFriendSegment(ContactSegment):
    def __init__(self, id: int) -> None:
        super().__init__(type="qq", id=id)

    data: _ContactFriendData


class ContactGroupSegment(ContactSegment):
    def __init__(self, id: int) -> None:
        super().__init__(type="group", id=id)

    data: _ContactGroupData


class _LocationData(TypedDict):
    lat: float
    lon: float
    title: NotRequired[str]
    content: NotRequired[str]


class LocationSegment(Segment[Literal["location"], _LocationData]):

    class Model(BaseModel):
        type: Literal["location"]
        data: _LocationData

    def __init__(
        self, lat: float, lon: float, title: str | None = None, content: str | None = None
    ) -> None:
        super().__init__(
            "location",
            cast(
                _LocationData,
                {"lat": lat, "lon": lon, "title": title, "content": content},
            ),
        )


class _MusicData(TypedDict):
    type: Literal["qq", "163", "xm"]
    id: str


class _MusicCustomData(TypedDict):
    type: Literal["custom"]
    url: AnyHttpUrl
    audio: AnyHttpUrl
    title: str
    content: NotRequired[str]
    image: NotRequired[AnyHttpUrl]


class MusicSegment(Segment[Literal["music"], _MusicData | _MusicCustomData]):

    class Model(BaseModel):
        type: Literal["music"]
        data: _MusicData | _MusicCustomData

    @overload
    def __init__(self, *, type: Literal["qq", "163", "xm"], id: str) -> None: ...

    @overload
    def __init__(
        self,
        *,
        type: Literal["custom"],
        url: AnyHttpUrl,
        audio: AnyHttpUrl,
        title: str,
        content: str | None = None,
        image: AnyHttpUrl | None = None,
    ) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        super().__init__("music", cast(_MusicData | _MusicCustomData, kv_pairs))


class MusicPlatformSegment(MusicSegment):
    def __init__(self, *, type: Literal["qq", "163", "xm"], id: str) -> None:
        super().__init__(type=type, id=id)

    data: _MusicData


class MusicCustomSegment(MusicSegment):
    def __init__(
        self,
        *,
        type: Literal["custom"],
        url: AnyHttpUrl,
        audio: AnyHttpUrl,
        title: str,
        content: str | None = None,
        image: AnyHttpUrl | None = None,
    ) -> None:
        super().__init__(
            type=type, url=url, audio=audio, title=title, content=content, image=image
        )

    data: _MusicCustomData


class _ReplyData(TypedDict):
    id: str


class ReplySegment(Segment[Literal["reply"], _ReplyData]):

    class Model(BaseModel):
        type: Literal["reply"]
        data: _ReplyData

    def __init__(self, id: str) -> None:
        super().__init__("reply", _ReplyData(id=id))


class _ForwardData(TypedDict):
    id: str


class ForwardSegment(Segment[Literal["forward"], _ForwardData]):

    class Model(BaseModel):
        type: Literal["forward"]
        data: _ForwardData

    def __init__(self, id: str) -> None:
        super().__init__("forward", _ForwardData(id=id))


class _NodeReferData(TypedDict):
    id: str


class _NodeStdCustomData(TypedDict):
    user_id: int
    nickname: str
    content: list[Segment.Model]


class _NodeGocqCustomData(TypedDict):
    uin: int
    name: str
    content: list[Segment.Model]


class NodeSegment(
    Segment[Literal["node"], _NodeReferData | _NodeStdCustomData | _NodeGocqCustomData]
):

    class Model(BaseModel):
        type: Literal["node"]
        data: _NodeReferData | _NodeStdCustomData | _NodeGocqCustomData

    @overload
    def __init__(self, *, id: str) -> None: ...

    @overload
    def __init__(
        self, *, uin: int, name: str, content: list[Segment], use_std: bool = False
    ) -> None: ...

    def __init__(self, **kv_pairs: Any) -> None:
        std: bool = kv_pairs.pop("use_std")
        id: str | None = kv_pairs.pop("id")

        if id:
            super().__init__("node", _NodeReferData(id=id))
        if not std:
            super().__init__(
                "node",
                _NodeGocqCustomData(
                    uin=kv_pairs["uin"],
                    name=kv_pairs["name"],
                    content=[seg._model for seg in kv_pairs["content"]],
                ),
            )
        else:
            super().__init__(
                "node",
                _NodeStdCustomData(
                    user_id=kv_pairs["uin"],
                    nickname=kv_pairs["name"],
                    content=[seg._model for seg in kv_pairs["content"]],
                ),
            )


class NodeReferSegment(NodeSegment):
    def __init__(self, id: str) -> None:
        super().__init__(id=id)

    data: _NodeReferData


class NodeStdCustomSegment(NodeSegment):
    def __init__(self, user_id: int, nickname: str, content: list[Segment]) -> None:
        super().__init__(uin=user_id, name=nickname, content=content, use_std=True)

    data: _NodeStdCustomData


class NodeGocqCustomSegment(NodeSegment):
    def __init__(self, uin: int, name: str, content: list[Segment]) -> None:
        super().__init__(uin=uin, name=name, content=content, use_std=False)

    data: _NodeGocqCustomData


class _XmlData(TypedDict):
    data: str


class XmlSegment(Segment[Literal["xml"], _XmlData]):

    class Model(BaseModel):
        type: Literal["xml"]
        data: _XmlData

    def __init__(self, data: str) -> None:
        super().__init__("xml", _XmlData(data=data))


class _JsonData(TypedDict):
    data: str


class JsonSegment(Segment[Literal["json"], _JsonData]):

    class Model(BaseModel):
        type: Literal["json"]
        data: _JsonData

    def __init__(self, data: str) -> None:
        super().__init__("json", _JsonData(data=data))
