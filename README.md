# TaskHub — Task Management API

Dự án học FastAPI theo lộ trình 8 ngày (64h), xây dựng dần một **Task Management API** duy nhất.
Mỗi ngày là một nhánh + một Pull Request.

**Trạng thái hiện tại: Day 1 — Core Setup & Architecture.**

## Yêu cầu môi trường

- [uv](https://docs.astral.sh/uv/) (quản lý Python 3.14 và dependencies)
- Docker (dùng từ Day 2 cho PostgreSQL)

## Cài đặt

```bash
uv sync
cp .env.example .env   # tuỳ chỉnh nếu cần
```

## Chạy ứng dụng

```bash
uv run uvicorn app.main:app --reload
```

| URL | Mô tả |
| --- | --- |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | OpenAPI schema |
| http://127.0.0.1:8000/api/v1/health | Health check |

## Kiểm tra chất lượng

```bash
uv run ruff check app tests
uv run ruff format --check app tests
uv run mypy app tests
uv run pytest
```

## Kiến trúc

Layered architecture, phụ thuộc một chiều `API → Service → Repository`:

```
app/
├── main.py                  # create_app(), lifespan, mount router
├── core/                    # cross-cutting: config, logging, exceptions, handlers, lifespan
├── api/
│   ├── deps.py              # DI providers (repository → service, pagination)
│   └── v1/
│       ├── router.py        # aggregate router, prefix /api/v1
│       └── endpoints/       # HTTP handlers, không chứa business logic
├── schemas/                 # Pydantic v2 request/response models
├── services/                # business logic, độc lập với HTTP
├── repositories/            # BaseRepository[T] + InMemoryRepository (Day 1)
└── models/                  # domain entities (Day 2: SQLAlchemy ORM)
```

- `core/exceptions.py` định nghĩa lỗi domain (`NotFoundError`, `ConflictError`, ...);
  `core/exception_handlers.py` map chúng sang HTTP, nên service không import FastAPI.
- Repository là generic `BaseRepository[T]`; Day 2 thay `InMemoryRepository` bằng
  implementation SQLAlchemy mà không sửa service/endpoint.
- `items` là resource scaffolding của Day 1, sẽ được thay bằng domain thật ở Day 2.

## API hiện có (Day 1)

| Method | Path | Mô tả | Mã thành công |
| --- | --- | --- | --- |
| GET | `/api/v1/health` | Health check | 200 |
| POST | `/api/v1/items` | Tạo item | 201 |
| GET | `/api/v1/items?page=&limit=` | Danh sách item (phân trang) | 200 |
| GET | `/api/v1/items/{item_id}` | Chi tiết item | 200 |
| PATCH | `/api/v1/items/{item_id}` | Cập nhật một phần | 200 |
| DELETE | `/api/v1/items/{item_id}` | Xoá item | 204 |

### Error envelope

Mọi lỗi trả về cùng một cấu trúc:

```json
{
  "error": {
    "code": "not_found",
    "message": "Item not found",
    "details": {"item_id": "00000000-0000-0000-0000-000000000000"}
  }
}
```

`code` gồm: `validation_error` (422), `not_found` (404), `conflict` (409),
`bad_request` (400), `http_error` (lỗi framework), `internal_error` (500).

## Lộ trình

| Ngày | Nội dung | Trạng thái |
| --- | --- | --- |
| 1 | Core Setup & Architecture | ✅ |
| 2 | Database: SQLAlchemy 2.x & Alembic | ⏳ |
| 3–7 | Business Logic & Core Features (auth, RBAC, cache, background task) | ⏳ |
| 8 | Review, Refactor & Optimization | ⏳ |

Các hạng mục ngoài phạm vi từng ngày được ghi tại [docs/BACKLOG.md](docs/BACKLOG.md).
