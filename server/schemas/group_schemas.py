from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    join_password: Optional[str] = Field(default=None, min_length=1, max_length=200)


class GroupResponse(BaseModel):
    id: int
    name: str
    owner: str
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class JoinRequestBody(BaseModel):
    password: Optional[str] = None
    message: Optional[str] = None


class JoinRequestResponse(BaseModel):
    id: int
    status: str
    model_config = {"from_attributes": True}


class GroupMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
