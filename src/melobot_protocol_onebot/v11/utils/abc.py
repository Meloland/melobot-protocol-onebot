from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Generic

from melobot.adapter.model import EventT
from melobot.exceptions import BotException
from melobot.typ import BetterABC, LogicMode, abstractmethod
from typing_extensions import Self


class UtilsError(BotException): ...


class Cloneable:
    def copy(self) -> Self:
        return deepcopy(self)


class BotChecker(BetterABC, Cloneable, Generic[EventT]):
    """检查器基类"""

    def __init__(self) -> None:
        super().__init__()

    def __and__(self, other: BotChecker[EventT]) -> BotChecker[EventT]:
        if not isinstance(other, BotChecker):
            raise UtilsError(f"联合检查器定义时出现了非检查器对象，其值为：{other}")
        return WrappedChecker(LogicMode.AND, self, other)

    def __or__(self, other: BotChecker[EventT]) -> BotChecker[EventT]:
        if not isinstance(other, BotChecker):
            raise UtilsError(f"联合检查器定义时出现了非检查器对象，其值为：{other}")
        return WrappedChecker(LogicMode.OR, self, other)

    def __invert__(self) -> BotChecker[EventT]:
        return WrappedChecker(LogicMode.NOT, self)

    def __xor__(self, other: BotChecker[EventT]) -> BotChecker[EventT]:
        if not isinstance(other, BotChecker):
            raise UtilsError(f"联合检查器定义时出现了非检查器对象，其值为：{other}")
        return WrappedChecker(LogicMode.XOR, self, other)

    @abstractmethod
    async def check(self, event: EventT) -> bool:
        """检查器检查方法

        任何检查器应该实现此抽象方法。

        :param event: 给定的事件
        :return: 检查是否通过
        """
        raise NotImplementedError

    @staticmethod
    def new(func: Callable[[EventT], bool]) -> BotChecker[EventT]:
        return CustomChecker[EventT](func)


class CustomChecker(BotChecker[EventT]):
    def __init__(self, func: Callable[[EventT], bool]) -> None:
        super().__init__()
        self.func = func

    async def check(self, event: EventT) -> bool:
        return self.func(event)


class WrappedChecker(BotChecker[EventT]):
    """合并检查器

    在两个 :class:`BotChecker` 对象间使用 | & ^ ~ 运算符即可返回合并检查器。

    .. admonition:: 提示
       :class: tip

       一般无需手动实例化该类，多数情况会直接使用本类对象，或将本类用作类型注解。
    """

    def __init__(
        self,
        mode: LogicMode,
        checker1: BotChecker[EventT],
        checker2: BotChecker[EventT] | None = None,
    ) -> None:
        """初始化一个合并检查器

        :param mode: 合并检查的逻辑模式
        :param checker1: 检查器1
        :param checker2: 检查器2
        """
        super().__init__()
        self.mode = mode
        self.c1, self.c2 = checker1, checker2

    async def check(self, event: EventT) -> bool:
        return LogicMode.calc(
            self.mode,
            await self.c1.check(event),
            (await self.c2.check(event)) if self.c2 is not None else None,
        )


class BotMatcher(BetterABC, Cloneable):
    """匹配器基类"""

    def __init__(self) -> None:
        super().__init__()

    def __and__(self, other: BotMatcher) -> WrappedMatcher:
        if not isinstance(other, BotMatcher):
            raise UtilsError(f"联合匹配器定义时出现了非匹配器对象，其值为：{other}")
        return WrappedMatcher(LogicMode.AND, self, other)

    def __or__(self, other: BotMatcher) -> WrappedMatcher:
        if not isinstance(other, BotMatcher):
            raise UtilsError(f"联合匹配器定义时出现了非匹配器对象，其值为：{other}")
        return WrappedMatcher(LogicMode.OR, self, other)

    def __invert__(self) -> WrappedMatcher:
        return WrappedMatcher(LogicMode.NOT, self)

    def __xor__(self, other: BotMatcher) -> WrappedMatcher:
        if not isinstance(other, BotMatcher):
            raise UtilsError(f"联合匹配器定义时出现了非匹配器对象，其值为：{other}")
        return WrappedMatcher(LogicMode.XOR, self, other)

    @abstractmethod
    async def match(self, text: str) -> bool:
        """匹配器匹配方法

        任何匹配器应该实现此抽象方法。

        :param text: 消息事件的文本内容
        :return: 是否匹配
        """
        raise NotImplementedError


class WrappedMatcher(BotMatcher):
    """合并匹配器

    在两个 :class:`BotMatcher` 对象间使用 | & ^ ~ 运算符即可返回合并匹配器

    .. admonition:: 提示
       :class: tip

       一般无需手动实例化该类，多数情况会直接使用本类对象，或将本类用作类型注解。
    """

    def __init__(
        self,
        mode: LogicMode,
        matcher1: BotMatcher,
        matcher2: BotMatcher | None = None,
    ) -> None:
        """初始化一个合并匹配器

        :param mode: 合并匹配的逻辑模式
        :param matcher1: 匹配器1
        :param matcher2: 匹配器2
        """
        super().__init__()
        self.mode = mode
        self.m1, self.m2 = matcher1, matcher2

    async def match(self, text: str) -> bool:
        return LogicMode.calc(
            self.mode,
            self.m1.match(text),
            self.m2.match(text) if self.m2 is not None else None,
        )


@dataclass
class ParseArgs:
    vals: list[Any]


class BotParser(BetterABC):
    """解析器基类

    解析器一般用作从消息文本中按规则批量提取参数
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def parse(self, text: str) -> ParseArgs | None:
        """解析方法

        任何解析器应该实现此抽象方法

        :param text: 消息文本内容
        :return: 解析结果

        """
        raise NotImplementedError
