from datetime import timedelta

from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, NameEmail

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.security import Token, verify_password, create_access_token

from config import config

router = APIRouter(prefix="/users", tags=["users"])

class ActiveTime(BaseModel):
    fromHour: int
    toHour: int

class PostUser(BaseModel):
    name: str
    pasword: str
    active_time: ActiveTime | None = None
    email: NameEmail | None = None
    telegram: str | None = None

class User(BaseModel):
    name: str
    active_time: ActiveTime | None = None

@router.post("/register")
def register_user(user: PostUser) -> User:
    pass

@router.get("/{user_id}")
def get_user(user_id: UUID) -> User:
    pass

# replace with actual usecase
def retrieve_user(db, username: str):
    pass

def authenticate_user(fake_db, username: str, password: str):
    user = retrieve_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

@router.post("/authorize")
def authorize_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(None, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.security.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
