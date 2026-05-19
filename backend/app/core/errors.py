"""共通エラー基盤。

Service層はHTTPを知らず、本モジュールの例外を `raise` する。
API層は原則 try/except を書かず、登録済みのハンドラに整形を委ねる。

レスポンス形は api-spec.md §1.4 準拠:
  {"error": {"code": str, "message": str, "details": list | None}}
"""

from __future__ import annotations

from typing import TypedDict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorDetail(TypedDict):
    """エラーレスポンスの `details` 配列の要素。

    - `field`: バリデーション対象のフィールド名（ドット区切り、ルートは空文字）
    - `message`: そのフィールドに対する人間可読なメッセージ
    """

    field: str
    message: str


class AppException(Exception):
    """アプリ共通の基底例外。"""

    def __init__(
        self,
        *,
        code: str,
        http_status: int,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message
        self.details = details


class NotFoundError(AppException):
    """リソースが存在しない (404)。"""

    def __init__(
        self,
        *,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            code="NOT_FOUND",
            http_status=status.HTTP_404_NOT_FOUND,
            message=message,
            details=details,
        )


class ConflictError(AppException):
    """一意制約違反など (409)。"""

    def __init__(
        self,
        *,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            code="CONFLICT",
            http_status=status.HTTP_409_CONFLICT,
            message=message,
            details=details,
        )


class BadRequestError(AppException):
    """その他の不正リクエスト (400)。"""

    def __init__(
        self,
        *,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            code="BAD_REQUEST",
            http_status=status.HTTP_400_BAD_REQUEST,
            message=message,
            details=details,
        )


def _build_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """共通ハンドラを FastAPI アプリに登録する。"""

    @app.exception_handler(AppException)
    async def _handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        return _build_response(
            status_code=exc.http_status,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details: list[ErrorDetail] = []
        for err in exc.errors():
            # `loc` は ("body", "name") のようなタプル。先頭のセクション名は除いて field とする。
            ignored = ("body", "query", "path")
            loc = [str(part) for part in err.get("loc", []) if part not in ignored]
            field = ".".join(loc) if loc else ""
            details.append({"field": field, "message": str(err.get("msg", ""))})

        return _build_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            message="入力値に誤りがあります",
            details=details,
        )
