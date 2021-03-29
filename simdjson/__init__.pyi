import json
from typing import (
    AbstractSet,
    Any,
    Dict,
    Final,
    Iterator,
    List,
    Literal,
    MutableMapping,
    NewType,
    Optional,
    Tuple,
    Union,
    ValuesView,
)


class Object(MutableMapping[Any, Any]):
    def __delitem__(self, key: Any) -> None:
        ...

    def __getitem__(self, key: Any) -> Any:
        ...

    def __setitem__(self, key: Any, value: Any) -> None:
        ...

    def __iter__(self) -> Iterator[Any]:
        ...

    def __len__(self) -> int:
        ...

    def as_dict(self) -> Dict[Any, Any]:
        ...

    def at_pointer(self, key: str) -> Any:
        ...

    def get(self, key: str, default: Any = None) -> Any:
        ...

    def keys(self) -> AbstractSet[Any]:
        ...

    def values(self) -> ValuesView[Any]:
        ...

    def items(self) -> AbstractSet[Tuple[Any, Any]]:
        ...

    @property
    def mini(self) -> 'Object':
        ...


Buffer = NewType('Buffer', bytes)


class Array(List[Any]):
    def count(self, v: Any) -> int:
        ...

    def as_list(self) -> List[Any]:
        ...

    def as_buffer(self, *, of_type: Literal['d', 'i', 'u']) -> Buffer:
        ...

    def at_pointer(self, key: str) -> Any:
        ...

    def index(
        self,
        x: Any,
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

    def load(self, path: str, recursive: bool = False) -> Union[Array, Object]:
        ...

    def parse(self, data: bytes, recursive: bool = False) -> Union[Array, Object]:
        ...


dumps = json.dumps
dump = json.dump

MAXSIZE_BYTES: Final[int]
PADDING: Final[int]
DEFAULT_MAX_DEPTH: Final[int]
VERSION: Final[str]
