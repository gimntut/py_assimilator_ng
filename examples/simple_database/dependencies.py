import sys
from typing import Any, Callable, Protocol, TypeAlias, TypedDict, cast

import pymongo
import redis
from bson import ObjectId
from sqlalchemy.orm import sessionmaker

from assimilator.core.usability.pattern_creator import create_uow
from examples.simple_database.models import AlchemyUser, InternalUser, MongoUser, RedisUser, engine

alchemy_session_creator = sessionmaker(bind=engine)
internal_session = {}


class BaseUser1(Protocol):
    id: str
    username: str
    email: str
    balance: float

    def __init__(self, *, username: str, email: str, balance: float = 0, id: str): ...


class BaseUser2(Protocol):
    id: ObjectId
    username: str
    email: str
    balance: float

    def __init__(self, *, _id: ObjectId, username: str, email: str, balance: float = 0, upsert: bool = False): ...


class BaseUser(Protocol):
    username: str
    email: str
    balance: float

    def __init__(self, *, username: str, email: str, balance: float = 0, upsert: bool = False): ...


class RegistryItem1(TypedDict):
    model: type[BaseUser1]
    session_creator: Callable
    kwargs_repository: dict[str, Any]


class RegistryItem2(TypedDict):
    model: type[BaseUser2]
    session_creator: Callable
    kwargs_repository: dict[str, Any]


RegistryItem: TypeAlias = RegistryItem1 | RegistryItem2

# Database registry contains all the possible patterns and their settings.
# We do that just as an example, you can try or do whatever you want!
database_registry: dict[str, RegistryItem] = {
    "alchemy": {
        "model": AlchemyUser,  # Model to be used
        "session_creator": lambda: alchemy_session_creator(),  # function that can create sessions
        "kwargs_repository": {},  # Additional settings for the repository
    },
    "internal": {
        "model": InternalUser,
        "session_creator": lambda: internal_session,
        "kwargs_repository": {},
    },
    "redis": {
        "model": RedisUser,
        "session_creator": lambda: redis.Redis(),
        "kwargs_repository": {},
    },
    "mongo": {
        "model": MongoUser,
        "session_creator": lambda: pymongo.MongoClient(),
        "kwargs_repository": {
            "database": "assimilator_users",
        },
    },
}

database_provider = sys.argv[1] if len(sys.argv) > 1 else "alchemy"  # get the provider from args
User: type[BaseUser] = cast(type[BaseUser], database_registry[database_provider]["model"])  # get the model


def get_uow():
    dependencies = database_registry[database_provider]
    model = dependencies["model"]
    session = dependencies["session_creator"]()  # create a new connection to the database
    kwargs_repository = dependencies["kwargs_repository"]

    return create_uow(
        provider=database_provider,
        model=model,
        session=session,
        kwargs_repository=kwargs_repository,
    )
