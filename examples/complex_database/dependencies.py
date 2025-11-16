import sys
from collections.abc import Sequence
from typing import Protocol

import pymongo
from redis.client import Redis
from sqlalchemy.orm import sessionmaker

from assimilator.alchemy.database import AlchemyRepository, AlchemyUnitOfWork
from assimilator.internal.database import InternalRepository, InternalUnitOfWork
from assimilator.mongo.database import MongoRepository, MongoUnitOfWork
from assimilator.redis_.database import RedisRepository, RedisUnitOfWork
from examples.complex_database.models import (
    AlchemyBalanceCurrency,
    AlchemyUser,
    AlchemyUserBalance,
    InternalBalance,
    InternalCurrency,
    InternalUser,
    MongoBalance,
    MongoCurrency,
    MongoUser,
    RedisBalance,
    RedisCurrency,
    RedisUser,
    engine,
)


class BaseBalance(Protocol):
    currency: str
    balance: int


class BaseUser(Protocol):
    id: str
    username: str
    email: str
    balance: float
    balances: Sequence[BaseBalance]

    def __init__(self, *, username: str, email: str, balance: float = 0, id: str): ...


if len(sys.argv) == 1 or sys.argv[1] == "alchemy":
    User = AlchemyUser
    Balance = AlchemyUserBalance
    Currency = AlchemyBalanceCurrency

    def get_uow():  # pyright: ignore[reportRedeclaration]
        DatabaseSession = sessionmaker(bind=engine)
        repository = AlchemyRepository(
            session=DatabaseSession(),
            model=User,
        )
        return AlchemyUnitOfWork(repository)

elif sys.argv[1] == "internal":
    User = InternalUser
    Balance = InternalBalance
    Currency = InternalCurrency
    internal_session = {}

    def get_uow():  # pyright: ignore[reportRedeclaration]
        repository = InternalRepository(internal_session, model=InternalUser)
        return InternalUnitOfWork(repository)

elif sys.argv[1] == "redis":
    redis_session = Redis()
    User = RedisUser
    Balance = RedisBalance
    Currency = RedisCurrency

    def get_uow():  # pyright: ignore[reportRedeclaration]
        repository = RedisRepository(redis_session, model=User)
        return RedisUnitOfWork(repository)

    redis_session.flushdb()

elif sys.argv[1] == "mongo":
    User = MongoUser
    Balance = MongoBalance
    Currency = MongoCurrency
    mongo_client = pymongo.MongoClient()

    mongo_client["assimilator_complex"].drop_collection(MongoUser.AssimilatorConfig.collection)

    def get_uow():
        repository = MongoRepository(session=mongo_client, model=User, database="assimilator_complex")
        return MongoUnitOfWork(repository)
