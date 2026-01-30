from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, PositiveFloat
from pydantic_extra_types.coordinate import Coordinate

from fastapi import APIRouter, Query

from api.security import AuthorizedUser

from model import Good as ModelGood, Area as ModelArea,  Message as ModelMessage, LookFilter as ModelLookFilter

from usecases.goods import GoodUsecase
from usecases.users import UserUsecase

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
    
class Message(BaseModel):
    message: str
    contact_info: str

class Area(BaseModel):
    place: Coordinate
    radius: PositiveFloat

class LookParams(BaseModel):
    name: str
    location: Area | None = None
    user_id: UUID | None = None

class GoodsList(BaseModel):
    array: list[Good]

def model_good_to_good(model_good: ModelGood) -> Good:
    return Good(id=model_good.id, name=model_good.name, description=model_good.description, price=model_good.price, 
                images=model_good.images, location=model_good.location, owner_id=model_good.owner_id)

def init(good_usecase: GoodUsecase, user_usecase: UserUsecase) -> APIRouter:
    router = APIRouter(prefix="/goods", tags=["goods"])

    @router.post("/publish")
    def publish_good(good: PostGood, current_user: AuthorizedUser) -> Good:
        model_good = ModelGood(
            id=None, 
            name=good.name,
            description=good.description,
            price=good.price,
            images=good.images,
            location=good.location,
            owner_id=current_user.id
        )
        model_good = good_usecase.publish_good(current_user.id, model_good)
        return model_good_to_good(model_good)

    @router.get("/{good_id}")
    def get_good(good_id: UUID) -> Good:
        model_good = good_usecase.get_good(good_id)
        return model_good_to_good(model_good)

    @router.post("/{good_id}")
    def update_good(good_id: UUID, good: PostGood, current_user: AuthorizedUser) -> Good:
        model_good = ModelGood(
            id=good_id,
            name=good.name,
            description=good.description,
            price=good.price,
            images=good.images,
            location=good.location,
            owner_id=current_user.id
        )
        model_good = good_usecase.update_good(current_user.id, good_id, model_good)
        return model_good_to_good(model_good)

    @router.delete("/{good_id}")
    def delete_good(good_id: UUID, current_user: AuthorizedUser):
        good_usecase.delete_good(current_user.id, good_id)

    @router.post("/{good_id}/message")
    def message_good_owner(good_id: UUID, message: Message, current_user: AuthorizedUser):
        model_message = ModelMessage(
            sender=current_user.id,
            recipient=None,
            good_id=good_id,
            message=message.message,
            contact_info=message.contact_info
        )
        user_usecase.message_owner(model_message)

    @router.get("/look")
    def look_good(look_query: Annotated[LookParams, Query()]) -> GoodsList:
        model_lf = ModelLookFilter(
            name=look_query.name,
            location=ModelArea(place=look_query.location.place, radius=look_query.location.radius),
            user_id=look_query.user_id
        )
        model_goods_list = good_usecase.look_good(model_lf)
        return GoodsList(array=[model_good_to_good(model_good) for model_good in model_goods_list.array])

    return router