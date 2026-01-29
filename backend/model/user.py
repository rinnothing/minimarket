from uuid import UUID

from pydantic import BaseModel, NameEmail

class ActiveTime(BaseModel):
    fromHour: int
    toHour: int

class User(BaseModel):
    id: UUID
    name: str
    hashed_pasword: str
    active_time: ActiveTime
    email: NameEmail
    telegram: str
    active: bool

def safe_print_user(user: User) -> User:
    user = user.model_copy(update={"hashed_password": None})
    return user
