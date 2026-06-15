from pydantic import BaseModel


class PageMeta(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False
    limit: int


class Page[T](BaseModel):
    data: list[T]
    page: PageMeta
