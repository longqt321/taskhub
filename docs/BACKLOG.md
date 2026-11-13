# Việc còn lại

Những phần chưa làm, để dành các ngày sau.

## Day 2

- SQLAlchemy 2.x async, model task thật, Alembic migration
- Repository bản SQLAlchemy, bỏ `InMemoryRepository`
- docker-compose chạy PostgreSQL trong container, không cài lên máy host
- `DATABASE_URL` bắt buộc, không để default trong code

## Day 3-4

- Auth: register, login, refresh, logout; JWT; hash password
- RBAC ADMIN/OWNER/EDITOR/VIEWER, kiểm tra quyền theo từng resource
- Model domain còn lại: workspaces, workspace_members, projects, labels, comments
- Thêm `project_id`, `assignee_id`, `created_by`, `priority`, `due_date` cho task

## Day 5-7

- Redis cache cho `GET /projects/{id}/tasks`, invalidate khi dữ liệu đổi
- Background task gửi mail khi assign task
- Swagger mô tả Bearer auth và error response đầy đủ
- Dockerfile multi-stage, docker compose chạy cả stack

## Sau này

- GitHub Actions chạy ruff + mypy + pytest
