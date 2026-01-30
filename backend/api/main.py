from fastapi import APIRouter

from api.routes import goods, users, confirm
from api import security

from usecases.users import UserUsecase 
from usecases.goods import GoodUsecase
from utils.late_executor import LateExecutor

def init(user_usecase: UserUsecase, good_usecase: GoodUsecase, late_executor: LateExecutor):
    api_router = APIRouter()
    security.init(None)

    api_router.include_router(goods.init(good_usecase, user_usecase))
    api_router.include_router(users.init(user_usecase))
    api_router.include_router(confirm.init(late_executor))
