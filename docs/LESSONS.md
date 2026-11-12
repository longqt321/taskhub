# Lessons

## L-001 — PATCH `{"name": null}` trả 500

- **Ngày:** 2026-11-11
- **Lỗi:** gửi `{"name": null}` vào `PATCH /api/v1/items/{id}` thì server trả 500.
- **Nguyên nhân:** `ItemUpdate` khai báo `name: str | None` nên không phân biệt được "không gửi field" với "gửi null". Service dùng `exclude_unset=True` nên ghi luôn `None` vào entity, tới lúc serialize response mới vỡ.
- **Cách sửa:** chặn null ngay trong schema bằng `model_validator`, trả 422. Field nullable như `description` vẫn cho null để xoá giá trị.

## L-002 — Ghi chuyện môi trường vào mục "Khó khăn" của báo cáo

- **Ngày:** 2026-11-13
- **Lỗi:** trong báo cáo intern ghi "Port 5432 bị chiếm nên phải đổi sang 5433" vào mục Khó khăn.
- **Nguyên nhân:** nhầm giữa vấn đề kỹ thuật nhỏ đã xử lý xong trong vài phút với khó khăn thực sự của quá trình làm việc. Mục Khó khăn dành cho thứ ảnh hưởng tiến độ hoặc cần hỗ trợ, không phải log chi tiết môi trường.
- **Cách phòng tránh:** trước khi ghi vào mục Khó khăn, tự hỏi: (1) đã giải quyết xong chưa, (2) có ảnh hưởng tiến độ hay cần ai giúp không. Nếu cả hai đều không thì bỏ qua, ghi N/A. Chi tiết kỹ thuật loại này chỉ cần comment trong code/README.
