# Việc còn lại

Những phần chưa làm, để dành các ngày sau.

## Day 4

- Model domain còn lại: workspaces, workspace_members, projects, labels, task_labels, comments
- Workspace CRUD (owner only), mời/xoá member, phân quyền OWNER/EDITOR/VIEWER
- Project CRUD trong workspace, archive project
- Kiểm tra quyền theo resource ownership, không chỉ theo role hệ thống
- Thêm `project_id`, `assignee_id`, `created_by`, `priority`, `due_date` cho task

## Day 5-7

- Task CRUD, assign, đổi status, priority, due_date
- Label CRUD và gán/bỏ label cho task
- Comment thêm/xoá trên task
- Redis cache cho `GET /projects/{id}/tasks`, invalidate khi dữ liệu đổi
- Background task gửi mail khi assign task
- Swagger mô tả Bearer auth và error response đầy đủ
- Dockerfile multi-stage, docker compose chạy cả stack

## Sau này

- GitHub Actions chạy ruff + mypy + pytest
- Test dùng transaction rollback thay vì tạo/drop bảng mỗi test
- Dọn refresh token hết hạn bằng job định kỳ
- Rate limit cho endpoint login
