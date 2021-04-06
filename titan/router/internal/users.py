from fastapi import APIRouter, Depends, HTTPException, status

from ...logger import logger
from ...settings.backends import users_db_internal
from ...tokens import DecodedToken
from ...utils import StrictBaseModel
from ..depends import get_decoded_token, store_decoded_token, validate_ttype_xaccess, empty_body

users_router_internal = APIRouter(
    prefix="/opt/user",
    dependencies=[
        Depends(store_decoded_token),
        Depends(validate_ttype_xaccess),
    ],
    tags=["internal/user"],
)


class FreezeEmailRequest(StrictBaseModel):
    email: str


@users_router_internal.post("/freeze/email")
async def freeze_email(request_data: FreezeEmailRequest):
    result = await users_db_internal.freeze_email(email=request_data.email)
    if result is None:
        logger.info(f"User freeze failed: (email={request_data.email}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: User freeze failed: (email={request_data.email})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"User frozen: (email={request_data.email})")


@users_router_internal.post("/unfreeze/email")
async def unfreeze_email(request_data: FreezeEmailRequest):
    result = await users_db_internal.unfreeze_email(email=request_data.email)
    if result is None:
        logger.info(f"User unfreeze failed: (email={request_data.email}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: User unfreeze failed: (email={request_data.email})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"User unfrozen:  (email={request_data.email})")


@users_router_internal.post("/freeze/user", dependencies=[Depends(empty_body)])
async def freeze_user(decoded_token: DecodedToken = Depends(get_decoded_token)):
    result = await users_db_internal.freeze_userid(userid=decoded_token.sub)
    if result is None:
        logger.info(f"User freeze failed: (user={decoded_token.sub}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: User freeze failed: (user={decoded_token.sub})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"User frozen: (user={decoded_token.sub})")


@users_router_internal.post("/unfreeze/user", dependencies=[Depends(empty_body)])
async def unfreeze_user(decoded_token: DecodedToken = Depends(get_decoded_token)):
    result = await users_db_internal.unfreeze_userid(userid=decoded_token.sub)
    if result is None:
        logger.info(f"User unfreeze failed: (user={decoded_token.sub}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: User unfreeze failed: (user={decoded_token.sub})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"User unfrozen: (user={decoded_token.sub})")
