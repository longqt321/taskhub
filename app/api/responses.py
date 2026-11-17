"""Khai báo response lỗi dùng lại cho các endpoint, để không lặp dict ở từng route."""

from typing import Any

from app.schemas.common import ErrorResponse

# kiểu của tham số responses= trong decorator của FastAPI
Responses = dict[int | str, dict[str, Any]]

UNAUTHORIZED: Responses = {401: {"model": ErrorResponse, "description": "Missing or invalid token"}}
FORBIDDEN: Responses = {403: {"model": ErrorResponse, "description": "Insufficient permissions"}}
VALIDATION_ERROR: Responses = {422: {"model": ErrorResponse, "description": "Validation error"}}
CONFLICT: Responses = {409: {"model": ErrorResponse, "description": "Resource already exists"}}


def not_found(description: str) -> Responses:
    return {404: {"model": ErrorResponse, "description": description}}


def bad_request(description: str) -> Responses:
    return {400: {"model": ErrorResponse, "description": description}}


def forbidden(description: str) -> Responses:
    return {403: {"model": ErrorResponse, "description": description}}


def conflict(description: str) -> Responses:
    return {409: {"model": ErrorResponse, "description": description}}
