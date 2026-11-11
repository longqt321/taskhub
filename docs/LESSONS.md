# Lessons

Ghi lại lỗi đã gặp, nguyên nhân gốc và cách phòng tránh. Mỗi mục có mã `L-###`.

<!--
Mẫu:

## L-001 — <tiêu đề ngắn>

- **Ngày:** YYYY-MM-DD
- **Lỗi:** <hiện tượng>
- **Nguyên nhân gốc:** <vì sao>
- **Cách phòng tránh:** <quy tắc để không lặp lại>
-->

Chưa có mục nào.

## L-001 — PATCH cho phép `null` ghi đè field non-nullable gây 500

- **Ngày:** 2026-11-11
- **Lỗi:** `PATCH /api/v1/items/{id}` với body `{"name": null}` trả 500
  (`ResponseValidationError`) thay vì lỗi 4xx.
- **Nguyên nhân gốc:** Schema `ItemUpdate` khai báo `name: str | None` để biểu diễn
  "không truyền thì giữ nguyên", nhưng không phân biệt được với "truyền null".
  Service dùng `model_dump(exclude_unset=True)` nên đã ghi `None` vào entity, phá
  invariant non-null và chỉ vỡ ở bước serialize response.
- **Cách phòng tránh:** Với PATCH, field non-nullable phải từ chối `null` ngay ở
  schema (`model_validator` kiểm tra `model_fields_set`), trả 422. Field nullable
  (`description`) vẫn cho phép `null` để xoá giá trị. Luôn có test cho case
  "truyền null vào field non-nullable".

