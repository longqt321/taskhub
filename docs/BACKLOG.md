# Việc còn lại

Những phần chưa làm, để dành các ngày sau.

## Day 6-7

- Redis cache cho `GET /tasks?project_id=...`, invalidate khi dữ liệu đổi
- Background task gửi mail khi assign task
- Swagger mô tả Bearer auth và error response đầy đủ
- Dockerfile multi-stage, docker compose chạy cả stack

## Sau này

- GitHub Actions chạy ruff + mypy + pytest
- Test dùng transaction rollback thay vì tạo/drop bảng mỗi test
- Dọn refresh token hết hạn bằng job định kỳ
- Rate limit cho endpoint login
