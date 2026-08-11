class ApplicationError(RuntimeError):
    """可由全局处理器安全转换为 HTTP 响应的应用异常。"""

    status_code = 500
    error_code = "internal_error"
    public_message = "服务器内部错误"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
