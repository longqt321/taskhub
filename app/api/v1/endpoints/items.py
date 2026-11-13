"""Endpoint CRUD cho items. Yêu cầu đăng nhập."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, ItemServiceDep, PaginationDep
from app.schemas.common import ErrorResponse, Page
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

_UNAUTHORIZED: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Missing or invalid token"}
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
    responses={
        **_UNAUTHORIZED,
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_item(payload: ItemCreate, service: ItemServiceDep, user: CurrentUser) -> ItemRead:
    item = await service.create(payload)
    return ItemRead.model_validate(item)


@router.get(
    "",
    summary="List items",
    responses={
        **_UNAUTHORIZED,
        422: {"model": ErrorResponse, "description": "Invalid pagination parameters"},
    },
)
async def list_items(
    service: ItemServiceDep, pagination: PaginationDep, user: CurrentUser
) -> Page[ItemRead]:
    items, total = await service.list(page=pagination.page, limit=pagination.limit)
    return Page[ItemRead].create(
        [ItemRead.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{item_id}",
    summary="Get an item",
    responses={
        **_UNAUTHORIZED,
        404: {"model": ErrorResponse, "description": "Item not found"},
    },
)
async def get_item(item_id: UUID, service: ItemServiceDep, user: CurrentUser) -> ItemRead:
    return ItemRead.model_validate(await service.get(item_id))


@router.patch(
    "/{item_id}",
    summary="Update an item",
    responses={
        **_UNAUTHORIZED,
        404: {"model": ErrorResponse, "description": "Item not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def update_item(
    item_id: UUID, payload: ItemUpdate, service: ItemServiceDep, user: CurrentUser
) -> ItemRead:
    return ItemRead.model_validate(await service.update(item_id, payload))


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
    responses={
        **_UNAUTHORIZED,
        404: {"model": ErrorResponse, "description": "Item not found"},
    },
)
async def delete_item(item_id: UUID, service: ItemServiceDep, user: CurrentUser) -> None:
    await service.delete(item_id)
