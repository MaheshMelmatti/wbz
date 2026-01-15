from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.db import create_user, get_user_by_email
from app.auth import authenticate_user, create_access_token, get_current_user, token_response

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- Request schemas ----------
class SignupRequest(BaseModel):
    email: str
    password: str


# ---------- Routes ----------

@router.post("/signup")
def signup(payload: SignupRequest):
    """
    Create a new user account.
    """
    # quick pre-check to fail fast on duplicates
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # attempt to create; convert domain errors to HTTP responses
    try:
        user = create_user(payload.email, payload.password)
        return {"id": user.id, "email": user.email, "created_at": str(user.created_at)}
    except ValueError as e:
        # expected client-side error (e.g. duplicate email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        # unexpected server error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Standard OAuth2 login. Returns JWT token.
    """
    return await token_response(form_data)


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    """
    Returns the authenticated user's profile.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": str(current_user.created_at)
    }


# Example of a protected route
@router.get("/protected/test")
async def protected_test(current_user=Depends(get_current_user)):
    return {"message": "You are authenticated", "user": current_user.email}
