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

# Message chung
MSG_VALIDATION_FAILED = "Request validation failed"
MSG_INTERNAL_ERROR = "Internal server error"
MSG_HTTP_ERROR = "Request could not be handled"
MSG_DEFAULT_BAD_REQUEST = "Bad request"
MSG_DEFAULT_NOT_FOUND = "Resource not found"
MSG_DEFAULT_CONFLICT = "Resource conflict"
MSG_NOT_AUTHENTICATED = "Not authenticated"
MSG_INSUFFICIENT_PERMISSIONS = "Insufficient permissions"

# Task
MSG_TASK_NOT_FOUND = "Task not found"
MSG_TITLE_CANNOT_BE_NULL = "title cannot be null"
MSG_STATUS_CANNOT_BE_NULL = "status cannot be null"
MSG_PRIORITY_CANNOT_BE_NULL = "priority cannot be null"
MSG_NAME_CANNOT_BE_NULL = "name cannot be null"

# Workspace và project
MSG_WORKSPACE_NOT_FOUND = "Workspace not found"
MSG_PROJECT_NOT_FOUND = "Project not found"
MSG_MEMBER_NOT_FOUND = "Member not found"
MSG_ASSIGNEE_NOT_FOUND = "Assignee not found"
MSG_NOT_WORKSPACE_MEMBER = "You are not a member of this workspace"
MSG_INSUFFICIENT_ROLE = "Your workspace role does not allow this action"
MSG_MEMBER_ALREADY_EXISTS = "User is already a member of this workspace"
MSG_OWNER_ROLE_RESERVED = "Workspace owner role cannot be assigned"
MSG_OWNER_CANNOT_BE_REMOVED = "Workspace owner cannot be removed or have their role changed"
MSG_PROJECT_ARCHIVED = "Archived project cannot be modified"
MSG_ASSIGNEE_NOT_IN_WORKSPACE = "Assignee must be a member of the workspace"

# Label và comment
MSG_LABEL_NOT_FOUND = "Label not found"
MSG_LABEL_ALREADY_EXISTS = "Label name already exists in this project"
MSG_LABEL_NOT_IN_PROJECT = "Label does not belong to the task's project"
MSG_LABEL_ALREADY_ATTACHED = "Label is already attached to this task"
MSG_LABEL_NOT_ATTACHED = "Label is not attached to this task"
MSG_COMMENT_NOT_FOUND = "Comment not found"
MSG_COMMENT_DELETE_FORBIDDEN = "Only the author or the workspace owner can delete this comment"
MSG_COMMENT_CANNOT_BE_EMPTY = "content cannot be empty"

# User và auth
MSG_USER_NOT_FOUND = "User not found"
MSG_FULL_NAME_CANNOT_BE_NULL = "full_name cannot be null"
MSG_EMAIL_ALREADY_REGISTERED = "Email already registered"
MSG_INCORRECT_CREDENTIALS = "Incorrect email or password"
MSG_INACTIVE_USER = "Account is disabled"
MSG_INVALID_TOKEN = "Invalid or expired token"
MSG_INVALID_REFRESH_TOKEN = "Invalid refresh token"
MSG_INACTIVE_USER_NOT_FOUND = "User not found or inactive"
MSG_INCORRECT_CURRENT_PASSWORD = "Incorrect current password"
MSG_CURRENT_PASSWORD_REQUIRED = "current_password là bắt buộc khi đổi password"
MSG_CURRENT_PASSWORD_WITHOUT_PASSWORD = "current_password chỉ có nghĩa khi đổi password"
MSG_PASSWORD_TOO_LONG = "password không được vượt quá {max_bytes} byte"

# Thao tác admin trên user
MSG_ADMIN_REQUIRED = "Chỉ admin mới được thực hiện thao tác này"
MSG_CANNOT_DELETE_SELF = "Không thể xoá hoặc khoá chính tài khoản đang đăng nhập"
MSG_CANNOT_DEMOTE_SELF = "Không thể tự hạ quyền admin của chính mình"
MSG_LAST_ADMIN = "Phải còn ít nhất một admin đang hoạt động"
