from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, PositiveFloat
from pydantic_extra_types.coordinate import Coordinate

from fastapi import APIRouter, Query

from api.security import AuthorizedUser

router = APIRouter(prefix="/goods", tags=["goods"])

class PostGood(BaseModel):
    name: str
    description: str | None = None
    price: float
    images: list[str]
    location: Coordinate | None = None
    
class Good(BaseModel):
    id: UUID
    name: str
    description: str
    price: float
    images: list[str]
    location: Coordinate | None = None
    owner_id: UUID

@router.post("/publish")
def publish_good(good: PostGood, current_user: AuthorizedUser) -> Good:
    pass

@router.get("/{good_id}")
def get_good(good_id: UUID) -> Good:
    pass

@router.post("/{good_id}")
def update_good(good_id: UUID, good: PostGood, current_user: AuthorizedUser) -> Good:
    pass

@router.delete("/{good_id}")
def delete_good(good_id: UUID, current_user: AuthorizedUser):
    pass

class Message(BaseModel):
    message: str
    contact_info: str

@router.post("/{good_id}/message")
def message_good_owner(good_id: UUID, message: Message, current_user: AuthorizedUser):
    pass

class Area(BaseModel):
    place: Coordinate
    radius: PositiveFloat

class LookParams(BaseModel):
    name: str
    location: Area | None = None
    user_id: UUID | None = None

def GoodsList(BaseModel):
    array: list[Good]

@router.get("/look")
def look_good(look_query: Annotated[LookParams, Query()]) -> GoodsList:
    pass
