from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from ...logger import logger
from ...settings.backends import apis_db_internal
from ...utils import ImmutBaseModel, StrictBaseModel
from ..depends import store_decoded_token, validate_ttype_xaccess

apis_router_internal = APIRouter(
    prefix="/opt/api",
    dependencies=[
        Depends(store_decoded_token),
        Depends(validate_ttype_xaccess),
    ],
    tags=["internal/api"],
)


class FreezeAPIRequest(StrictBaseModel):
    userid: UUID4
    apislug: str


@apis_router_internal.post("/freeze")
async def freeze(request_data: FreezeAPIRequest):
    result = await apis_db_internal.freeze(
        userid=request_data.userid,
        apislug=request_data.apislug,
    )
    if result is None:
        logger.info(f"API freeze failed: (user={request_data.userid}, apislug={request_data.apislug}) does not exist.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: API freeze failed: (user={request_data.userid}, apislug={request_data.apislug})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"API frozen: (user={request_data.userid}, apislug={request_data.apislug})")


@apis_router_internal.post("/unfreeze")
async def unfreeze(request_data: FreezeAPIRequest):
    result = await apis_db_internal.unfreeze(
        userid=request_data.userid,
        apislug=request_data.apislug,
    )
    if result is None:
        logger.info(
            f"API unfreeze failed: (user={request_data.userid}, apislug={request_data.apislug}) does not exist."
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result is False:
        logger.info(f"Unexpected: API unfreeze failed: (user={request_data.userid}, apislug={request_data.apislug})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error")
    logger.info(f"API unfrozen: (user={request_data.userid}, apislug={request_data.apislug})")


class GetAllRequest(StrictBaseModel):
    userid: UUID4


class APIResponse(ImmutBaseModel):
    apislug: str
    userid: UUID4
    frozen: bool
    deleted: bool
    disabled: bool
    created_at: datetime
    updated_at: datetime
    description: str


class GetAllResponse(ImmutBaseModel):
    apis: list[APIResponse]


@apis_router_internal.post("", response_model=GetAllResponse)
async def get_all(request_data: GetAllRequest):
    result = await apis_db_internal.get_all(userid=request_data.userid)
    logger.info(f"List API request: (userid={request_data.userid})")
    return result
