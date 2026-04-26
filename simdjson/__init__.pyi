import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Final,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    overload,
)

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

Primitives = Union[int, float, str, bool]
JSONScalar = Optional[Primitives]
SimValue = Union['Object', 'Array', JSONScalar]
UnboxedValue = Union[JSONScalar, Dict[str, Any], List[Any]]
ParseInput = Union[str, bytes, bytearray, memoryview]
PathInput = Union[str, bytes, Path]
KeyInput = Union[str, bytes]
_Default = TypeVar('_Default')


class Object:
    parser: 'Parser'

    def __getitem__(self, key: KeyInput) -> SimValue:
        ...

    def __iter__(self) -> Iterator[str]:
        ...

    def __len__(self) -> int:
        ...

    def __contains__(self, key: object) -> bool:
        ...

    def as_dict(self) -> Dict[str, UnboxedValue]:
        ...

    def at_pointer(self, key: KeyInput) -> SimValue:
        ...

    def keys(self) -> Iterator[str]:
        ...

    def values(self) -> Iterator[UnboxedValue]:
        ...

    def items(self) -> Iterator[Tuple[str, UnboxedValue]]:
        ...

    @overload
    def get(self, key: KeyInput) -> Optional[SimValue]:
        ...

    @overload
    def get(self, key: KeyInput, default: _Default) -> Union[SimValue, _Default]:
        ...

    @property
    def mini(self) -> bytes:
        ...


class Array:
    parser: 'Parser'

    def __len__(self) -> int:
        ...

    @overload
    def __getitem__(self, idx: int) -> SimValue:
        ...

    @overload
    def __getitem__(self, idx: slice) -> List[UnboxedValue]:
        ...

    def __iter__(self) -> Iterator[SimValue]:
        ...

    def as_list(self) -> List[UnboxedValue]:
        ...

    def as_buffer(self, *, of_type: Literal['d', 'i', 'u']) -> Any:
        ...

    def at_pointer(self, key: KeyInput) -> SimValue:
        ...

    @property
    def mini(self) -> bytes:
        ...


class Parser:
    def __init__(self, max_capacity: int = ...) -> None:
        ...

    def get_implementations(
        self,
        supported_by_runtime: bool = ...
    ) -> Iterator[Tuple[str, str]]:
        ...

    @property
    def implementation(self) -> Tuple[str, str]:
        ...

    @implementation.setter
    def implementation(self, name: str) -> None:
        ...

    @overload
    def load(
        self,
        path: PathInput,
        recursive: Literal[False] = ...,
    ) -> SimValue:
        ...

    @overload
    def load(
        self,
        path: PathInput,
        recursive: Literal[True],
    ) -> UnboxedValue:
        ...

    @overload
    def parse(
        self,
        data: ParseInput,
        recursive: Literal[False] = ...,
    ) -> SimValue:
        ...

    @overload
    def parse(
        self,
        data: ParseInput,
        recursive: Literal[True],
    ) -> UnboxedValue:
        ...


dumps = json.dumps
dump = json.dump
JSONEncoder = json.JSONEncoder

def loads(
    s: ParseInput,
    *,
    cls: Any = ...,
    object_hook: Any = ...,
    parse_float: Any = ...,
    parse_int: Any = ...,
    parse_constant: Any = ...,
    object_pairs_hook: Any = ...,
    **kwargs: Any,
) -> UnboxedValue:
    ...

def load(
    fp: Any,
    *,
    cls: Any = ...,
    object_hook: Any = ...,
    parse_float: Any = ...,
    parse_int: Any = ...,
    parse_constant: Any = ...,
    object_pairs_hook: Any = ...,
    **kwargs: Any,
) -> UnboxedValue:
    ...

MAXSIZE_BYTES: Final[int] = ...
PADDING: Final[int] = ...
VERSION: Final[str] = ...
