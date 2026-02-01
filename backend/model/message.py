from uuid import UUID

from pydantic import BaseModel, PositiveFloat

class Message(BaseModel):
    sender: UUID
    recipient: UUID
    good_id: UUID
    message: str
    contact_info: str
