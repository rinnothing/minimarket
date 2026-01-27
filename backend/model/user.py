from pydantic import BaseModel, NameEmail

class ActiveTime(BaseModel):
    fromHour: int
    toHour: int

class User(BaseModel):
    name: str
    hashed_pasword: str
    active_time: ActiveTime | None = None
    email: NameEmail | None = None
    telegram: str | None = None
