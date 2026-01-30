from datetime import timedelta

from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, NameEmail

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.security import Token, create_access_token, AuthorizedUser
from utils.security import verify_password

from usecases.users import UserUsecase

from model import User as ModelUser, ActiveTime as ModelActiveTime

from config import config

class ActiveTime(BaseModel):
    from_hour: int
    to_hour: int

class CreateUser(BaseModel):
    name: str
    pasword: str
    active_time: ActiveTime | None = None
    email: NameEmail | None = None
    telegram: str | None = None

class User(BaseModel):
    name: str
    active_time: ActiveTime | None = None

class UpdateConfirmation(BaseModel):
    email: NameEmail | None = None
    telegram: str | None = None

def model_user_to_user(model_user: ModelUser) -> User:
    return User(name=model_user.name, active_time=ActiveTime(from_hour=model_user.active_time.from_hour, 
                                                             to_hour=model_user.active_time.to_hour))

def init(user_usecase: UserUsecase) -> APIRouter:
    router = APIRouter(prefix="/users", tags=["users"])
    
    @router.post("/register")
    def register_user(user: CreateUser) -> User:
        model_user = ModelUser(
            id = None,
            name = user.name,
            hashed_pasword = None,
            active_time = ModelActiveTime(from_hour=user.active_time.from_hour, to_hour=user.active_time.to_hour),
            email = user.email,
            telegram = user.telegram,
            active = False
        )
        model_user = user_usecase.register_user(model_user, user.pasword)
        return model_user_to_user(model_user)

    @router.get("/{user_id}")
    def get_user(user_id: UUID) -> User:
        model_user = user_usecase.get_user(user_id)
        return model_user_to_user(model_user)

    @router.get("/username/{username}")
    def get_user_by_username(username: str) -> User:
        model_user = user_usecase.get_by_username(username)
        return model_user_to_user(model_user)

    def authenticate_user(username: str, password: str):
        user = user_usecase.get_by_username(username)
        if not user:
            return False
        if not verify_password(password, user.hashed_pasword):
            return False
        return user

    @router.post("/authorize")
    def authorize_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=config.security.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.name}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    @router.post("/update")
    def update_user(user: User, current_user: AuthorizedUser) -> User:
        model_user = user_usecase.update_user_info(current_user.id, user.name, 
            None if not user.active_time else ModelActiveTime(from_hour=user.active_time.from_hour, 
                                                              to_hour=user.active_time.to_hour))
        return model_user_to_user(model_user)

    @router.post("/change-password")
    def change_password(old_password: str, new_password: str, current_user: AuthorizedUser):
        user_usecase.change_password(current_user.id, old_password, new_password)

    @router.post("/reset-password")
    def reset_password(username: str):
        user_usecase.reset_password(username)

    @router.post("/update-confirmation")
    def update_confirmation(new_confirmation: UpdateConfirmation, current_user: AuthorizedUser):
        user_usecase.update_confirmation(current_user.id, new_confirmation.email, new_confirmation.telegram)

    return router
