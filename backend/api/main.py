from fastapi import APIRouter

from api.routes import goods, users

api_router = APIRouter()
api_router.include_router(goods.router)
api_router.include_router(users.router)
