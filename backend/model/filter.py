from uuid import UUID

from pydantic import BaseModel, PositiveFloat
from pydantic_extra_types.coordinate import Coordinate

class Area(BaseModel):
    place: Coordinate
    radius: PositiveFloat

class LookFilter(BaseModel):
    name: str
    location: Area | None = None
    user_id: UUID | None = None
    