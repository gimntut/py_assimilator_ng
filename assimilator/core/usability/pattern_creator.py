from typing import TypeVar, Any, Type, Dict

from assimilator.core.usability.registry import get_pattern
from assimilator.core.database import Repository, UnitOfWork
from assimilator.core.services import CRUDService

ModelT = TypeVar("ModelT")


def create_repository(
    provider: str,
    model: type[ModelT],
    session: Any,
    kwargs_repository: Dict[str, Any] = None,
) -> Repository:
    repository_cls: type[Repository] = get_pattern(provider=provider, pattern_name='repository')
    return repository_cls(model=model, session=session, **(kwargs_repository or {}))


def create_uow(
    provider: str,
    model: type[ModelT],
    session: Any,
    kwargs_repository: Dict[str, Any] = None,
    kwargs_uow: Dict[str, Any] = None,
) -> UnitOfWork:
    repository = create_repository(
        provider=provider,
        model=model,
        session=session,
        kwargs_repository=kwargs_repository,
    )
    uow_cls: type[UnitOfWork] = get_pattern(provider=provider, pattern_name='uow')
    return uow_cls(repository=repository, **(kwargs_uow or {}))


def create_crud(
    provider: str,
    model: type[ModelT],
    session: Any,
    kwargs_repository: Dict[str, Any] = None,
    kwargs_uow: Dict[str, Any] = None,
) -> CRUDService:
    uow = create_uow(
        provider=provider,
        model=model,
        session=session,
        kwargs_repository=kwargs_repository,
        kwargs_uow=kwargs_uow,
    )
    crud_cls: type[CRUDService] = get_pattern(provider=provider, pattern_name='crud')
    return crud_cls(uow=uow)
