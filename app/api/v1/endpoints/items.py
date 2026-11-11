"""Endpoint CRUD cho items."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import ItemServiceDep, PaginationDep
from app.schemas.common import ErrorResponse, Page
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
    responses={422: {"model": ErrorResponse, "description": "Validation error"}},
)
async def create_item(payload: ItemCreate, service: ItemServiceDep) -> ItemRead:
    item = await service.create(payload)
    return ItemRead.model_validate(item)


@router.get(
    "",
    summary="List items",
    responses={422: {"model": ErrorResponse, "description": "Invalid pagination parameters"}},
)
async def list_items(service: ItemServiceDep, pagination: PaginationDep) -> Page[ItemRead]:
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
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
async def get_item(item_id: UUID, service: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(await service.get(item_id))


@router.patch(
    "/{item_id}",
    summary="Update an item",
    responses={
        404: {"model": ErrorResponse, "description": "Item not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def update_item(item_id: UUID, payload: ItemUpdate, service: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(await service.update(item_id, payload))


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
async def delete_item(item_id: UUID, service: ItemServiceDep) -> None:
    await service.delete(item_id)
