from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from ...logger import logger
from ...settings.backends import admins_db_internal
from ...utils import StrictBaseModel
from ..depends import store_decoded_token, validate_ttype_xaccess

admins_router_internal = APIRouter(
    prefix="/opt/x",
    dependencies=[
        Depends(store_decoded_token),
        Depends(validate_ttype_xaccess),
    ],
    tags=["internal/admin"],
)


class FreezeUsernameRequest(StrictBaseModel):
    username: str


@admins_router_internal.post("/freeze/username")
async def freeze_username(request_data: FreezeUsernameRequest):
    result = await admins_db_internal.freeze_username(username=request_data.username)
    if result is None:
        logger.info(f"Admin freeze failed: (username={request_data.username}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: Admin freeze failed: (username={request_data.username})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"Admin frozen: (username={request_data.username})")


@admins_router_internal.post("/unfreeze/username")
async def unfreeze_username(request_data: FreezeUsernameRequest):
    result = await admins_db_internal.unfreeze_username(username=request_data.username)
    if result is None:
        logger.info(f"Admin unfreeze failed: (username={request_data.username}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: Admin unfreeze failed: (username={request_data.username})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"Admin unfrozen:  (username={request_data.username})")


class FreezeAdminidRequest(StrictBaseModel):
    adminid: UUID4


@admins_router_internal.post("/freeze/admin")
async def freeze_admin(request_data: FreezeAdminidRequest):
    result = await admins_db_internal.freeze_adminid(adminid=request_data.adminid)
    if result is None:
        logger.info(f"Admin freeze failed: (admin={request_data.adminid}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: Admin freeze failed: (admin={request_data.adminid})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"Admin frozen: (admin={request_data.adminid})")


@admins_router_internal.post("/unfreeze/admin")
async def unfreeze_admin(request_data: FreezeAdminidRequest):
    result = await admins_db_internal.unfreeze_adminid(adminid=request_data.adminid)
    if result is None:
        logger.info(f"Admin unfreeze failed: (admin={request_data.adminid}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: Admin unfreeze failed: (admin={request_data.adminid})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"Admin unfrozen: (admin={request_data.adminid})")


class CreateAdminRequest(StrictBaseModel):
    email: str
    username: str
    password: str
    scope: str


@admins_router_internal.post("")
async def create(request_data: CreateAdminRequest):
    result = await admins_db_internal.create(**request_data.dict())
    if result is None:
        logger.info(f"Admin create failed: ({request_data.dict()})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(
            f"Admin create failed: username already exists (email={request_data.email}, username={request_data.username})"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    logger.info(f"Admin create: (email={request_data.email}, username={request_data.username})")
