from typing import Protocol, TypeVar

from assimilator.core.database.repository import Repository

ModelT = TypeVar("ModelT")


class ICurrency(Protocol):
    currency: str
    country: str

    def __init__(self, *, id: str, currency: str, country: str) -> None: ...


class IBalance(Protocol):
    currency: ICurrency
    balance: float | int

    def __init__(self, *, id: str, currency: ICurrency, balance: float): ...


class IUser(Protocol):
    id: str
    username: str
    email: str
    balance: float
    balances: list[IBalance]

    def __init__(self, *, username: str, email: str, balance: float = 0, id: str): ...


class IUnitOfWork(Protocol):
    repository: Repository

    def __enter__(self) -> "IUnitOfWork": ...
    def __exit__(self, exc_type, exc_val, exc_tb): ...
    def commit(self) -> None: ...
    def begin(self): ...
    def rollback(self): ...
    def close(self): ...
    def __init__(self) -> None: ...
