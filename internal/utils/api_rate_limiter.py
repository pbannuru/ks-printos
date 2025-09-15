from starlette.requests import Request
from slowapi import Limiter
from uuid import uuid4


def custom_rate_limit(request: Request):
    return request.user.uuid


limiter = Limiter(
    key_func=custom_rate_limit,
)
