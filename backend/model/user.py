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
