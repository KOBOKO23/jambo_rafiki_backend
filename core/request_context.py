from contextvars import ContextVar


_request_id_ctx_var: ContextVar[str] = ContextVar('request_id', default='-')


def set_request_id(request_id: str):
    return _request_id_ctx_var.set(request_id)


def get_request_id() -> str:
    return _request_id_ctx_var.get()


def reset_request_id(token) -> None:
    _request_id_ctx_var.reset(token)
