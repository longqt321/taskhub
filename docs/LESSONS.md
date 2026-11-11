# Lessons

## L-001 — PATCH `{"name": null}` trả 500

- **Ngày:** 2026-11-11
- **Lỗi:** gửi `{"name": null}` vào `PATCH /api/v1/items/{id}` thì server trả 500.
- **Nguyên nhân:** `ItemUpdate` khai báo `name: str | None` nên không phân biệt được "không gửi field" với "gửi null". Service dùng `exclude_unset=True` nên ghi luôn `None` vào entity, tới lúc serialize response mới vỡ.
- **Cách sửa:** chặn null ngay trong schema bằng `model_validator`, trả 422. Field nullable như `description` vẫn cho null để xoá giá trị.
