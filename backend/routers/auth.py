from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from auth import create_access_token
from config import APP_PASSWORD, APP_USERNAME

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if body.username != APP_USERNAME or body.password != APP_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=body.username)
    return TokenResponse(access_token=token)
