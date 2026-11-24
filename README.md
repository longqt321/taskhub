# TaskHub

API quản lý công việc viết bằng FastAPI (PostgreSQL, Redis, Alembic, JWT, RBAC), hoàn thiện qua 8 ngày từ khởi tạo đến review và đóng gói Docker.

## Chạy

Cần uv (Python 3.14) và Docker.

```bash
docker compose up -d          # postgres 16, host port 5433
uv sync
cp .env.example .env          # nhớ đổi SECRET_KEY
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Swagger ở http://127.0.0.1:8000/docs, ReDoc ở http://127.0.0.1:8000/redoc.

Port 5433 vì 5432 trên máy đã có Postgres khác chạy. Đổi được trong `docker-compose.yml` và `DATABASE_URL`.

## Biến môi trường

Xem mẫu tại [.env.example](.env.example). Các biến chính:

| Biến | Bắt buộc | Mặc định | Mô tả |
| --- | --- | --- | --- |
| `DATABASE_URL` | có | - | Chuỗi kết nối Postgres (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | có | - | Khoá ký JWT (tối thiểu 32 bytes) |
| `ENVIRONMENT` | không | `local` | `local` / `staging` / `production` (tắt Swagger khi `production`) |
| `DEBUG` | không | `false` | Bật/tắt chế độ debug |
| `LOG_LEVEL` | không | `INFO` | Mức log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `API_V1_PREFIX` | không | `/api/v1` | Prefix của toàn bộ API v1 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | không | `30` | Thời hạn access token (phút) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | không | `7` | Thời hạn refresh token (ngày) |
| `REDIS_URL` | không | - | URL Redis cache (`redis://localhost:6379/0`); bỏ trống nếu không dùng cache |
| `CACHE_TTL_SECONDS` | không | `60` | TTL cache danh sách task (giây) |
| `POSTGRES_USER` | không | `taskhub` | User Postgres dùng trong `docker-compose.yml` |
| `POSTGRES_PASSWORD` | không | `taskhub` | Mật khẩu Postgres dùng trong `docker-compose.yml` |
| `POSTGRES_DB` | không | `taskhub` | Tên database Postgres dùng trong `docker-compose.yml` |

## Migration

```bash
uv run alembic revision --autogenerate -m "mô tả thay đổi"
uv run alembic upgrade head
uv run alembic downgrade -1
```

`migrations/env.py` lấy URL từ `app.core.config` và metadata từ `app.models` nên thêm model mới chỉ cần export trong `app/models/__init__.py`.

## Kiểm tra code

Cần Postgres đang chạy và database `taskhub_test`:

```bash
docker exec taskhub-db psql -U taskhub -d taskhub -c "CREATE DATABASE taskhub_test OWNER taskhub;"
uv run ruff check app tests
uv run mypy app tests
uv run pytest
```

Test tạo bảng bằng metadata rồi drop sau mỗi test, không đụng DB dev.

## Cấu trúc

```
app/
├── main.py
├── core/          # config, logging, exception, constants, messages, pagination, database, security, lifespan
├── api/           # router, dependency, endpoint
├── schemas/       # pydantic model
├── services/      # nghiệp vụ
├── repositories/  # truy cập dữ liệu
└── models/        # model SQLAlchemy
migrations/        # alembic
```

Luồng gọi: endpoint → service → repository. Service không import FastAPI, lỗi nghiệp vụ raise `AppError` rồi handler đổi sang HTTP response.

`BaseRepository` là interface chung, `SqlAlchemyRepository` là bản cài đặt. Engine và session factory tạo một lần trong lifespan, mỗi request được cấp một session riêng.

Quy ước:

- Chuỗi trả về client và mã lỗi nằm trong `app/core/messages.py`.
- Giới hạn độ dài, phân trang nằm trong `app/core/constants.py`.
- Schema kế thừa `BaseSchema` để tự strip khoảng trắng và đọc được từ ORM object.

## Auth

- Mật khẩu băm bằng argon2 (`pwdlib`), không lưu plaintext.
- Access token 30 phút, refresh token 7 ngày. Refresh token lưu `jti` vào DB để thu hồi được.
- `POST /auth/refresh` xoay vòng: thu hồi token cũ và ghi token mới trong cùng một transaction, revoke bằng `UPDATE ... WHERE revoked_at IS NULL RETURNING`. Dùng lại token đã revoke trả 401 và cắt luôn mọi session của user đó.
- Đổi mật khẩu hoặc bị admin khoá tài khoản thì toàn bộ refresh token cũ mất giá trị.
- Token có claim `type` (access/refresh), `jti`, `iat`; decode kiểm tra `type` nên refresh token không dùng được như access token. `sub` hỏng trả 401, không để 500.
- `get_current_user` là chỗ duy nhất đọc Bearer token, kiểm tra user còn tồn tại và `is_active`. 401 luôn kèm header `WWW-Authenticate: Bearer`.
- `RequireRoles(...)` kiểm tra role hệ thống; ADMIN luôn được đi qua. Thiếu quyền trả 403.
- Mật khẩu giới hạn 8 ký tự tối thiểu và 72 **byte** tối đa (giới hạn của bcrypt), không phải 72 ký tự.
- Sửa/xoá user là thao tác của ADMIN: không tự xoá hay tự khoá chính mình, và luôn phải còn ít nhất một admin đang hoạt động.

## Workspace và project

- Tạo workspace thì người tạo tự động là OWNER, ghi vào `workspace_members` trong cùng transaction.
- Role trong workspace: OWNER sửa/xoá workspace và mời member, EDITOR tạo/sửa project và task, VIEWER chỉ đọc.
- `app/services/access.py` là nơi kiểm tra quyền. ADMIN hệ thống được qua mọi bước, user thường phải là member workspace.
- Project thuộc workspace. Archive chỉ đổi `status` sang ARCHIVED; xoá project cần OWNER.
- Task bắt buộc có `project_id`, kèm `assignee_id`, `created_by`, `priority` và `due_date`. `GET /tasks` trả task thuộc các workspace mình là member, hoặc lọc theo `?project_id=...`.

## Label và comment

- Label thuộc một project, tên không trùng trong cùng project (ràng buộc `uq_labels_project_id_name`), màu dạng `#RRGGBB`.
- Gắn/bỏ label bằng `PUT`/`DELETE /tasks/{task_id}/labels/{label_id}`. Label phải cùng project với task, gắn hai lần trả 409.
- Comment thuộc một task. Ai đọc được task thì đọc và viết comment được; xoá comment thì tác giả hoặc OWNER workspace, ADMIN đi qua.
- `GET /tasks` nhận thêm `assignee_id`, `status`, `priority`, `due_before`, `due_after`, `search` (tìm trong tiêu đề). Các điều kiện ghép bằng AND, giá trị enum sai trả 422.

## Docker chạy cả stack

```bash
SECRET_KEY=change-me-to-a-random-32-byte-secret docker compose up --build -d
```

Service `migrate` chạy `alembic upgrade head` trước khi `api` khởi động trên port `8000`. Tài liệu Swagger ở `/docs` (bật `persistAuthorization` để giữ Bearer token khi tải lại trang, tự động tắt khi `ENVIRONMENT=production`).

## Cache và background task

- `GET /tasks?project_id=...` kiểm tra quyền trước rồi đọc/ghi Redis theo từng trang và bộ lọc (`CACHE_TTL_SECONDS`, mặc định 60 giây). Nếu không cấu hình `REDIS_URL` hoặc Redis lỗi, app tự bỏ qua cache để không ảnh hưởng luồng chính.
- Cache của project bị xoá ngay khi tạo/sửa/xoá task hoặc sửa/xoá/gắn/bỏ label trong project đó.
- Khi tạo task có `assignee_id` hoặc cập nhật đổi sang người nhận mới, `BackgroundTasks` chạy `send_task_assigned_email` sau khi trả response.

## API

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/health` | không |
| POST | `/api/v1/auth/register` | không |
| POST | `/api/v1/auth/login` | không |
| POST | `/api/v1/auth/refresh` | không |
| POST | `/api/v1/auth/logout` | không |
| GET | `/api/v1/users/me` | Bearer |
| PATCH | `/api/v1/users/me` | Bearer |
| GET | `/api/v1/users?page=1&limit=20` | Bearer + ADMIN |
| GET | `/api/v1/users/{id}` | Bearer + ADMIN |
| PATCH | `/api/v1/users/{id}` | Bearer + ADMIN |
| DELETE | `/api/v1/users/{id}` | Bearer + ADMIN |
| POST | `/api/v1/workspaces` | Bearer |
| GET | `/api/v1/workspaces` | Bearer |
| GET | `/api/v1/workspaces/{id}` | Bearer, member |
| PATCH | `/api/v1/workspaces/{id}` | OWNER |
| DELETE | `/api/v1/workspaces/{id}` | OWNER |
| GET | `/api/v1/workspaces/{id}/members` | Bearer, member |
| POST | `/api/v1/workspaces/{id}/members` | OWNER |
| PATCH | `/api/v1/workspaces/{id}/members/{user_id}` | OWNER |
| DELETE | `/api/v1/workspaces/{id}/members/{user_id}` | OWNER |
| POST | `/api/v1/workspaces/{id}/projects` | EDITOR |
| GET | `/api/v1/workspaces/{id}/projects` | Bearer, member |
| GET | `/api/v1/projects/{id}` | Bearer, member |
| PATCH | `/api/v1/projects/{id}` | EDITOR |
| POST | `/api/v1/projects/{id}/archive` | EDITOR |
| DELETE | `/api/v1/projects/{id}` | OWNER |
| POST | `/api/v1/tasks` | EDITOR |
| GET | `/api/v1/tasks?project_id=...` | Bearer, member |
| GET | `/api/v1/tasks/{id}` | Bearer, member |
| PATCH | `/api/v1/tasks/{id}` | EDITOR |
| DELETE | `/api/v1/tasks/{id}` | EDITOR |
| POST | `/api/v1/projects/{id}/labels` | EDITOR |
| GET | `/api/v1/projects/{id}/labels` | Bearer, member |
| PATCH | `/api/v1/labels/{id}` | EDITOR |
| DELETE | `/api/v1/labels/{id}` | EDITOR |
| GET | `/api/v1/tasks/{id}/labels` | Bearer, member |
| PUT | `/api/v1/tasks/{id}/labels/{label_id}` | EDITOR |
| DELETE | `/api/v1/tasks/{id}/labels/{label_id}` | EDITOR |
| GET | `/api/v1/tasks/{id}/comments` | Bearer, member |
| POST | `/api/v1/tasks/{id}/comments` | Bearer, member |
| DELETE | `/api/v1/tasks/{id}/comments/{comment_id}` | tác giả hoặc OWNER |

Task có `title`, `description`, `status` (TODO / IN_PROGRESS / IN_REVIEW / DONE), `priority` (LOW / MEDIUM / HIGH / URGENT), `project_id`, `assignee_id`, `created_by`, `due_date` và danh sách `labels`.

Lỗi trả về cùng một dạng:

```json
{
  "error": {
    "code": "not_found",
    "message": "Task not found",
    "details": {"task_id": "00000000-0000-0000-0000-000000000000"}
  }
}
```

`code` có thể là `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `bad_request`, `http_error`, `internal_error`.

## Việc còn lại

Xem [docs/BACKLOG.md](docs/BACKLOG.md).
