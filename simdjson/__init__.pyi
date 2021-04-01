import json
from typing import (
    AbstractSet,
    Any,
    Dict,
    Final,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    ValuesView,
    overload,
)

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

Primitives = Union[int, float, str, bool]
SimValue = Optional[Union['Object', 'Array', Primitives]]
UnboxedValue = Optional[Union[Primitives, Dict[str, Any], List[Any]]]


class Object(Mapping[str, SimValue]):
    def __getitem__(self, key: str) -> SimValue:
        ...

    def __iter__(self) -> Iterator[str]:
        ...

    def __len__(self) -> int:
        ...

    def as_dict(self) -> Dict[str, UnboxedValue]:
        ...

    def at_pointer(self, key: str) -> SimValue:
        ...

    def keys(self) -> AbstractSet[str]:
        ...

    def values(self) -> ValuesView[SimValue]:
        ...

    def items(self) -> AbstractSet[Tuple[str, SimValue]]:
        ...

    @property
    def mini(self) -> 'Object':
        ...


class Array(Sequence[SimValue]):
    def __len__(self) -> int:
        ...

    def __getitem__(self, idx: Union[int, slice]) -> 'Array':
        ...

    def count(self, v: SimValue) -> int:
        ...

    def as_list(self) -> List[Optional[Union[Primitives, dict, list]]]:
        ...

    def as_buffer(self, *, of_type: Literal['d', 'i', 'u']) -> bytes:
        ...

    def at_pointer(self, key: str) -> SimValue:
        ...

    def index(
        self,
        x: SimValue,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> int:
        ...

    @property
    def mini(self) -> 'Array':
        ...

    @property
    def slots(self) -> int:
        ...


class Parser:
    def __init__(self, max_capacity: int = ...) -> None:
        ...

    @overload
    def load(
        self,
        path: str,
        recursive: Literal[False],
    ) -> SimValue:
        ...

    @overload
    def load(
        self,
        path: str,
        recursive: Literal[True],
    ) -> UnboxedValue:
        ...

    @overload
    def parse(
        self,
        data: bytes,
        recursive: Literal[False],
    ) -> SimValue:
        ...

    @overload
    def parse(
        self,
        data: bytes,
        recursive: Literal[True],
    ) -> UnboxedValue:
        ...


dumps = json.dumps
dump = json.dump

MAXSIZE_BYTES: Final[int]
PADDING: Final[int]
DEFAULT_MAX_DEPTH: Final[int]
VERSION: Final[str]
