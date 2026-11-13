# TaskHub

API quản lý công việc viết bằng FastAPI, làm dần qua 8 ngày học. Hiện xong Day 3: có đăng ký/đăng nhập bằng JWT, refresh token xoay vòng, phân quyền theo role.

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
├── core/          # config, logging, exception, database, security, lifespan
├── api/           # router, dependency, endpoint
├── schemas/       # pydantic model
├── services/      # nghiệp vụ
├── repositories/  # truy cập dữ liệu
└── models/        # model SQLAlchemy
migrations/        # alembic
```

Luồng gọi: endpoint → service → repository. Service không import FastAPI, lỗi nghiệp vụ raise `AppError` rồi handler đổi sang HTTP response.

`BaseRepository` là interface chung, `SqlAlchemyRepository` là bản cài đặt. Engine và session factory tạo một lần trong lifespan, mỗi request được cấp một session riêng.

## Auth

- Mật khẩu băm bằng argon2 (`pwdlib`), không lưu plaintext.
- Access token 30 phút, refresh token 7 ngày. Refresh token lưu `jti` vào DB để thu hồi được.
- `POST /auth/refresh` xoay vòng: token cũ bị revoke, cấp cặp mới. Dùng lại token cũ trả 401.
- `get_current_user` đọc Bearer token, kiểm tra user còn tồn tại và `is_active`.
- `RequireRoles(...)` kiểm tra role; ADMIN luôn được đi qua. Thiếu quyền trả 403.

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
| POST | `/api/v1/items` | Bearer |
| GET | `/api/v1/items?page=1&limit=20` | Bearer |
| GET | `/api/v1/items/{id}` | Bearer |
| PATCH | `/api/v1/items/{id}` | Bearer |
| DELETE | `/api/v1/items/{id}` | Bearer |

Lỗi trả về cùng một dạng:

```json
{
  "error": {
    "code": "not_found",
    "message": "Item not found",
    "details": {"item_id": "00000000-0000-0000-0000-000000000000"}
  }
}
```

`code` có thể là `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `bad_request`, `http_error`, `internal_error`.

## Việc còn lại

Xem [docs/BACKLOG.md](docs/BACKLOG.md).
