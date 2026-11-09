import json
from os import PathLike
from typing import (
    Any,
    Dict,
    Final,
    Iterator,
    List,
    Literal,
    Optional,
    SupportsIndex,
    Tuple,
    TypeVar,
    Union,
    overload,
)

Primitives = Union[int, float, str, bool]
JSONScalar = Optional[Primitives]
SimValue = Union['Object', 'Array', JSONScalar]
UnboxedValue = Union[JSONScalar, Dict[str, Any], List[Any]]
ParseInput = Union[str, bytes, bytearray, memoryview]
PathInput = Union[str, bytes, PathLike[str], PathLike[bytes]]
KeyInput = Union[str, bytes]
_Default = TypeVar('_Default')


class Object:
    @property
    def parser(self) -> 'Parser':
        ...

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

    def at_pointer(self, json_pointer: KeyInput) -> SimValue:
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
    @property
    def parser(self) -> 'Parser':
        ...

    def __len__(self) -> int:
        ...

    @overload
    def __getitem__(self, key: SupportsIndex) -> SimValue:
        ...

    @overload
    def __getitem__(self, key: slice) -> List[UnboxedValue]:
        ...

    def __iter__(self) -> Iterator[SimValue]:
        ...

    def as_list(self) -> List[UnboxedValue]:
        ...

    def as_buffer(self, *, of_type: Literal['d', 'i', 'u']) -> Any:
        ...

    def at_pointer(self, json_pointer: KeyInput) -> SimValue:
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
        src: ParseInput,
        recursive: Literal[False] = ...,
    ) -> SimValue:
        ...

    @overload
    def parse(
        self,
        src: ParseInput,
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
