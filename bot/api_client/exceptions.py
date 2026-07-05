class ApiError(Exception):
    """Базовое исключение — любая ошибка при обращении к API основного сайта."""


class ApiTimeout(ApiError):
    pass


class ApiUnauthorized(ApiError):
    pass


class ApiNotFound(ApiError):
    pass


class ApiServerError(ApiError):
    """5xx на стороне основного сайта."""
