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


Primitives = Union[int, float, str, boolean]
K = str
V = Union['Object', 'Array', Primitives]


class Object(Mapping[K, V]):
  
    def __getitem__(self, key: K) -> V:
        ...

    def __iter__(self) -> Iterator[V]:
        ...

    def __len__(self) -> int:
        ...

    def as_dict(self) -> Dict[K, V]:
        ...

    def at_pointer(self, key: str) -> V:
        ...

    def get(self, key: K, default: Optional[V] = None) -> V:
        ...

    def keys(self) -> AbstractSet[K]:
        ...

    def values(self) -> ValuesView[V]:
        ...

    def items(self) -> AbstractSet[Tuple[K, V]]:
        ...

    @property
    def mini(self) -> 'Object':
        ...


Buffer = NewType('Buffer', bytes)


class Array(Sequence[V]):
    def count(self, v: V) -> int:
        ...

    def as_list(self) -> List[V]:
        ...

    def as_buffer(self, *, of_type: Literal['d', 'i', 'u']) -> Buffer:
        ...

    def at_pointer(self, key: str) -> V:
        ...

    def index(
        self,
        x: V,
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
