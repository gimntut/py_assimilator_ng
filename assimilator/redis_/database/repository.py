import json
from collections.abc import Iterable, Sized
from typing import List, Optional, TypeVar, cast

from redis import Redis
from redis.client import Pipeline
from redis.typing import KeyT

from assimilator.core.database import BaseModel, LazyCommand, Repository, SpecificationType
from assimilator.core.database.exceptions import DataLayerError, InvalidQueryError, MultipleResultsError, NotFoundError
from assimilator.core.patterns.error_wrapper import ErrorWrapper
from assimilator.internal.database import InternalSpecificationList
from assimilator.internal.database.models_utils import dict_to_internal_models

RedisModelT = TypeVar("RedisModelT", bound=BaseModel)


class RedisRepository(Repository[Redis, RedisModelT, str, InternalSpecificationList]):
    session: Redis
    transaction: Pipeline | Redis

    def __init__(
        self,
        session: Redis,
        model: type[RedisModelT],
        initial_query: Optional[str] = "",
        specifications=InternalSpecificationList,
        error_wrapper: Optional[ErrorWrapper] = None,
        use_double_filter: bool = True,
    ):
        super(RedisRepository, self).__init__(
            session=session,
            model=model,
            initial_query=initial_query,
            specifications=specifications,
            error_wrapper=error_wrapper or ErrorWrapper(default_error=DataLayerError, skipped_errors=(NotFoundError,)),
        )
        self.transaction = session
        self.use_double_specifications = use_double_filter

    # type: ignore
    def get(
        self,
        *specifications: SpecificationType,
        lazy: bool = False,
        initial_query: Optional[str] = None,
    ) -> LazyCommand[RedisModelT] | RedisModelT:
        query = self._apply_specifications(query=initial_query, specifications=specifications) or "*"
        keys = cast(KeyT, self.session.keys(query))
        found_objects = cast(Iterable, self.session.mget(keys))

        if not all(found_objects):
            raise NotFoundError(f"{self} repository get() did not find any results with this query: {query}")

        parsed_objects = list(
            self._apply_specifications(
                query=[self.model.loads(found_object) for found_object in found_objects],  # type: ignore
                specifications=specifications,
            )
        )

        if not parsed_objects:
            raise NotFoundError(f"{self} repository get() did not find any results with this query: {query}")
        elif len(parsed_objects) != 1:
            print(*parsed_objects, sep="\n\t *** ")
            raise MultipleResultsError(f"{self} repository get() did not find any results with this query: {query}")
        return cast(RedisModelT, parsed_objects[0])

    def filter(
        self,
        *specifications: SpecificationType,
        lazy: bool = False,
        initial_query: Optional[str] = None,
    ) -> LazyCommand[List[RedisModelT]] | List[RedisModelT]:
        if self.use_double_specifications and specifications:
            key_name = (
                self._apply_specifications(
                    query=initial_query,
                    specifications=specifications,
                )
                or "*"
            )
        else:
            key_name = "*"
        keys = cast(KeyT, self.session.keys(key_name))
        models = cast(Iterable, self.session.mget(keys))

        if isinstance(self.model, BaseModel):
            query = [self.model.loads(value) for value in models]
        else:
            query = [self.model(**json.loads(value)) for value in models]

        return cast(list[RedisModelT], list(self._apply_specifications(specifications=specifications, query=query)))  # type: ignore

    def dict_to_models(self, data: dict) -> RedisModelT:
        return self.model(**dict_to_internal_models(data=data, model=self.model))

    def save(self, obj: Optional[RedisModelT] = None, **obj_data) -> RedisModelT:
        if obj is None:
            obj = self.dict_to_models(data=obj_data)

        self.transaction.set(
            name=obj.id,
            value=obj.json(),
            ex=getattr(obj, "expire_in", None),  # for Pydantic model compatability
            px=getattr(obj, "expire_in_px", None),
            nx=getattr(obj, "only_create", False),
            xx=getattr(obj, "only_update", False),
            keepttl=getattr(obj, "keep_ttl", False),
        )
        return obj

    def delete(self, obj: Optional[RedisModelT] = None, *specifications: SpecificationType) -> None:
        obj, clear_specifications = self._check_obj_is_specification(obj, specifications)

        if clear_specifications:
            models = cast(list[RedisModelT], self.filter(*clear_specifications))
            self.transaction.delete(*[str(model.id) for model in models])
        elif obj is not None:
            self.transaction.delete(obj.id)

    def update(
        self,
        obj: Optional[RedisModelT] = None,
        *specifications: SpecificationType,
        **update_values,
    ) -> None:
        obj, clear_specifications = self._check_obj_is_specification(obj, specifications)

        if clear_specifications:
            if not update_values:
                raise InvalidQueryError(
                    "You did not provide any update_values to the update() yet provided specifications"
                )

            models = cast(list[RedisModelT], self.filter(*clear_specifications, lazy=False))
            updated_models = {}

            for model in models:
                model.__dict__.update(update_values)
                updated_models[str(model.id)] = model.json()

            self.transaction.mset(updated_models)

        elif obj is not None:
            obj.only_update = True
            self.save(obj)

    def is_modified(self, obj: RedisModelT) -> bool | None:
        if self.specifications is None:
            return False
        return self.get(self.specifications.filter(obj.id), lazy=False) == obj

    def refresh(self, obj: RedisModelT) -> None:
        if self.specifications is None:
            return
        fresh_obj = self.get(self.specifications.filter(obj.id), lazy=False)

        for key, value in fresh_obj.dict().items():
            setattr(obj, key, value)

    def count(
        self,
        *specifications: SpecificationType,
        lazy: bool = False,
        initial_query: Optional[str] = None,
    ) -> LazyCommand[int] | int:
        if not specifications:
            return cast(int, self.session.dbsize())

        filter_query = self._apply_specifications(
            query=initial_query,
            specifications=specifications,
        )
        keys = cast(Sized, self.session.keys(filter_query))
        return len(keys)


__all__ = [
    "RedisRepository",
]
