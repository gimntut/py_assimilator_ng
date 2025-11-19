from typing import Generic, Protocol, TypeVar

ModelT = TypeVar("ModelT")


class ICurrency(Protocol):
    currency: str
    country: str

    def __init__(self, currency: str, country: str) -> None: ...


class IBalance(Protocol):
    currency: ICurrency
    balance: float | int

    def __init__(self, currency: ICurrency, balance: float): ...


class IUser(Protocol):
    id: str
    username: str
    email: str
    balance: float
    balances: list[IBalance]

    def __init__(self, *, username: str, email: str, balance: float = 0, id: str): ...


class IRepository(Generic[ModelT]):
    def save(self, *args, **kwargs): ...
    def get(self) -> ModelT: ...


class IUnitOfWork(Protocol):
    repository: IRepository

    def commit(self) -> None: ...
    def __enter__(self) -> "IUnitOfWork": ...
    def __exit__(self, exc_type, exc_val, exc_tb): ...
