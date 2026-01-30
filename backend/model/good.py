from uuid import UUID

from pydantic import BaseModel
from pydantic_extra_types.coordinate import Coordinate

class Good(BaseModel):
    id: UUID
    name: str
    description: str
    price: float
    images: list[str]
    location: Coordinate | None = None
    owner_id: UUID

class GoodsList(BaseModel):
    array: list[Good]
