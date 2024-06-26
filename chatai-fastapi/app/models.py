from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str


class UserInDB(User):
    hashed_password: str


class Chat(BaseModel):
    title: str | None = None
    conversation_id: str | None = None
    message: str
