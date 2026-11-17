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
MSG_PRIORITY_CANNOT_BE_NULL = "priority cannot be null"
MSG_NAME_CANNOT_BE_NULL = "name cannot be null"

MSG_WORKSPACE_NOT_FOUND = "Workspace not found"
MSG_PROJECT_NOT_FOUND = "Project not found"
MSG_MEMBER_NOT_FOUND = "Member not found"
MSG_USER_NOT_FOUND = "User not found"
MSG_ASSIGNEE_NOT_FOUND = "Assignee not found"

MSG_NOT_WORKSPACE_MEMBER = "You are not a member of this workspace"
MSG_INSUFFICIENT_ROLE = "Your workspace role does not allow this action"
MSG_MEMBER_ALREADY_EXISTS = "User is already a member of this workspace"
MSG_OWNER_ROLE_RESERVED = "Workspace owner role cannot be assigned"
MSG_OWNER_CANNOT_BE_REMOVED = "Workspace owner cannot be removed or have their role changed"
