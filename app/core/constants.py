"""Giới hạn độ dài và phân trang dùng chung."""

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_NAME_LENGTH = 200
MAX_LABEL_LENGTH = 50
MAX_COLOR_LENGTH = 7
MAX_COMMENT_LENGTH = 2000

MIN_PAGE = 1
MIN_LIMIT = 1
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# bcrypt chỉ dùng 72 byte đầu của mật khẩu, tính theo byte chứ không phải ký tự
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72

# HS256 cần khoá đủ dài, ngắn hơn thì coi như cấu hình sai
MIN_SECRET_KEY_BYTES = 32
