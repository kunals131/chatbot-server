from pydantic import BaseModel

class AuthTokenData(BaseModel):
    username: str = None
    id: str = None