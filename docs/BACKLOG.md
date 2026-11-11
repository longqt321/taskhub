# Backlog

Các hạng mục phát sinh hoặc bị đẩy lùi, không làm lén trong ngày hiện tại.

## Từ Day 1 (Core Setup & Architecture)

| Hạng mục | Lý do hoãn | Dự kiến |
| --- | --- | --- |
| SQLAlchemy 2.x async + Alembic + models domain thật | Thuộc Session 2 | Day 2 |
| Thay `InMemoryRepository` bằng repository SQLAlchemy | Cần DB trước | Day 2 |
| `docker-compose.yml` với PostgreSQL (chạy trong Docker, không cài lên host) | Cần DB trước | Day 2 |
| Auth: register/login/refresh/logout, JWT, password hashing | Thuộc Session 3 | Day 3 |
| RBAC (ADMIN/OWNER/EDITOR/VIEWER), resource ownership | Thuộc Session 3–4 | Day 3–4 |
| Redis caching + invalidation cho `GET /projects/{id}/tasks` | Thuộc Session 5 | Day 5 |
| Background task gửi email khi assign task | Thuộc Session 6 | Day 6 |
| Swagger Bearer auth scheme + mô tả error responses đầy đủ | Cần auth trước | Day 3+ |
| Dockerfile multi-stage + `docker compose up` full stack | Thuộc Session 7 | Day 7 |
| GitHub Actions CI (ruff + mypy + pytest) | Ngoài phạm vi đề bài | Sau Day 8 (nếu cần) |
| Xoá resource `items` scaffolding | Chờ domain thật | Day 2 |
