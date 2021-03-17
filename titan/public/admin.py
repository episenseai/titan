from devtools import debug
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

admin_router = APIRouter(prefix="/x", tags=["x"])

oauth2_bearer_token = OAuth2PasswordBearer(tokenUrl="/x/token")


# separate admin table
# column -> email (from main users table, identifies the admin)
#        -> amdin_username
#        -> admin_pass
#        -> scope (different power levels of the admin)
#        -> disabled (if the account is disabled or not)
@admin_router.post("/token")
async def get_access_token(
    token: str = Depends(oauth2_bearer_token),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    pass
