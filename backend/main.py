from fastapi import FastAPI
from fastapi.routing import APIRoute

from config import config

from api import main as main_router

api_router = main_router.init(None, None, None)

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title=config.name,
    openapi_url=f"{config.oapi.oapi_path}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.include_router(api_router)
