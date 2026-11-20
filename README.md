# TaskHub

API quản lý công việc viết bằng FastAPI, làm dần qua 8 ngày học. Hiện xong Day 2: có Postgres, SQLAlchemy async và Alembic, CRUD `tasks` lưu thật xuống DB.

## Chạy

Cần uv (Python 3.14) và Docker.

```bash
docker compose up -d          # postgres 16, host port 5433
uv sync
cp .env.example .env
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

`migrations/env.py` lấy URL từ `app.core.config` nên không cần sửa `alembic.ini`.

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
├── core/          # config, logging, exception, constants, messages, pagination, database, lifespan
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

## API

| Method | Path |
| --- | --- |
| GET | `/api/v1/health` |
| POST | `/api/v1/tasks` |
| GET | `/api/v1/tasks?page=1&limit=20` |
| GET | `/api/v1/tasks/{id}` |
| PATCH | `/api/v1/tasks/{id}` |
| DELETE | `/api/v1/tasks/{id}` |

Task có `title`, `description`, `status` (TODO / IN_PROGRESS / IN_REVIEW / DONE). `project_id`, `assignee_id`, `created_by` sẽ thêm ở Day 4 khi có workspace và auth.

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

`code` có thể là `validation_error`, `not_found`, `conflict`, `bad_request`, `http_error`, `internal_error`.

## Việc còn lại

Xem [docs/BACKLOG.md](docs/BACKLOG.md).
