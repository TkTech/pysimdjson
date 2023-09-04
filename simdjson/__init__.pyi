import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Final,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

Primitives = Union[int, float, str, bool]
SimValue = Optional[Primitives]
UnboxedValue = Optional[Union[Primitives, Dict[str, Any], List[Any]]]


class Parser:
    def __init__(self, max_capacity: int = ...) -> None:
        ...

    def get_implementations(
        self,
        supported_by_runtime: Literal[True] = ...
    ) -> Sequence[Tuple[str, str]]:
        ...

    @property
    def implementation(self) -> Tuple[str, str]:
        ...

    @implementation.setter
    def implementation(self, name: str):
        ...

    @overload
    def load(
        self,
        path: Union[str, Path]
    ) -> SimValue:
        ...

    @overload
    def load(
        self,
        path: Union[str, Path]
    ) -> UnboxedValue:
        ...

    @overload
    def parse(
        self,
        data: Union[str, bytes, bytearray, memoryview]
    ) -> SimValue:
        ...

    @overload
    def parse(
        self,
        data: Union[str, bytes, bytearray, memoryview]
    ) -> UnboxedValue:
        ...


dumps = json.dumps
dump = json.dump


def loads(s, *, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None, **kw): ...


def load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
         parse_constant=None, object_pairs_hook=None, **kwargs): ...


MAXSIZE_BYTES: Final[int] = ...
PADDING: Final[int] = ...
VERSION: Final[str] = ...
