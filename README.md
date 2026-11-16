# TaskHub

API quản lý công việc viết bằng FastAPI, làm dần qua 8 ngày học. Hiện mới xong Day 1: dựng khung project và CRUD mẫu cho resource `tasks`.

## Chạy

Cần uv (Python 3.14).

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Swagger ở http://127.0.0.1:8000/docs, ReDoc ở http://127.0.0.1:8000/redoc.

## Kiểm tra code

```bash
uv run ruff check app tests
uv run mypy app tests
uv run pytest
```

## Cấu trúc

```
app/
├── main.py
├── core/          # config, logging, exception, constants, messages, pagination, lifespan
├── api/           # router, dependency, endpoint
├── schemas/       # pydantic model
├── services/      # nghiệp vụ
├── repositories/  # truy cập dữ liệu
└── models/        # entity
```

Luồng gọi: endpoint → service → repository. Service không import FastAPI, lỗi nghiệp vụ raise `AppError` rồi handler đổi sang HTTP response.

`BaseRepository` là interface chung, hiện chỉ có `InMemoryRepository`. Sang Day 2 thêm bản SQLAlchemy rồi bỏ bản in-memory, service và endpoint giữ nguyên.

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
