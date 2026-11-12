"""Chuỗi trả về cho client, gom một chỗ để không hardcode rải rác."""

# Mã lỗi trong error envelope
CODE_VALIDATION_ERROR = "validation_error"
CODE_UNAUTHORIZED = "unauthorized"
CODE_FORBIDDEN = "forbidden"
CODE_NOT_FOUND = "not_found"
CODE_CONFLICT = "conflict"
CODE_BAD_REQUEST = "bad_request"
CODE_HTTP_ERROR = "http_error"
CODE_INTERNAL_ERROR = "internal_error"

# Message
MSG_VALIDATION_FAILED = "Request validation failed"
MSG_INTERNAL_ERROR = "Internal server error"
MSG_TASK_NOT_FOUND = "Task not found"
MSG_TITLE_CANNOT_BE_NULL = "title cannot be null"
MSG_STATUS_CANNOT_BE_NULL = "status cannot be null"
