"""Endpoint CRUD cho project. Project nằm trong workspace nên quyền theo workspace."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, PaginationDep, ProjectServiceDep
from app.api.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR, not_found
from app.core.messages import MSG_PROJECT_NOT_FOUND
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(tags=["projects"])

_NOT_FOUND = not_found(MSG_PROJECT_NOT_FOUND)


@router.post(
    "/workspaces/{workspace_id}/projects",
    status_code=status.HTTP_201_CREATED,
    summary="Create a project in a workspace",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def create_project(
    workspace_id: UUID, payload: ProjectCreate, service: ProjectServiceDep, user: CurrentUser
) -> ProjectRead:
    return ProjectRead.model_validate(await service.create(user, workspace_id, payload))


@router.get(
    "/workspaces/{workspace_id}/projects",
    summary="List projects in a workspace",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def list_projects(
    workspace_id: UUID,
    service: ProjectServiceDep,
    pagination: PaginationDep,
    user: CurrentUser,
) -> Page[ProjectRead]:
    projects, total = await service.list(user, workspace_id, pagination)
    return Page[ProjectRead].create(
        [ProjectRead.model_validate(project) for project in projects],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/projects/{project_id}",
    summary="Get a project",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def get_project(
    project_id: UUID, service: ProjectServiceDep, user: CurrentUser
) -> ProjectRead:
    return ProjectRead.model_validate(await service.get(user, project_id))


@router.patch(
    "/projects/{project_id}",
    summary="Update a project",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def update_project(
    project_id: UUID, payload: ProjectUpdate, service: ProjectServiceDep, user: CurrentUser
) -> ProjectRead:
    return ProjectRead.model_validate(await service.update(user, project_id, payload))


@router.post(
    "/projects/{project_id}/archive",
    summary="Archive a project",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def archive_project(
    project_id: UUID, service: ProjectServiceDep, user: CurrentUser
) -> ProjectRead:
    return ProjectRead.model_validate(await service.archive(user, project_id))


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (workspace owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_project(project_id: UUID, service: ProjectServiceDep, user: CurrentUser) -> None:
    await service.delete(user, project_id)
