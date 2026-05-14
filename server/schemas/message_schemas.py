from datetime import datetime
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    content:   str = Field(min_length=1, max_length=2000)
    recipient: str = Field(min_length=3, max_length=50)


class MessageResponse(BaseModel):
    id:         int
    sender:     str
    recipient:  str
    content:    str
    created_at: datetime

    model_config = {"from_attributes": True}
