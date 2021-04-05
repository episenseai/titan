from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import UUID4, Field

from ...logger import logger
from ...models.public.apis import APIState
from ...settings.backends import apis_db
from ...tokens import DecodedToken
from ...utils import ImmutBaseModel, StrictBaseModel
from ..depends import empty_body, get_decoded_token, store_decoded_token, validate_ttype_access

apis_router = APIRouter(
    prefix="/api",
    tags=["api"],
    dependencies=[
        Depends(store_decoded_token),
        Depends(validate_ttype_access),
    ],
)


class GETAPIResponse(ImmutBaseModel):
    apislug: str
    userid: UUID4
    disabled: bool
    created_at: datetime
    updated_at: datetime
    description: str


@apis_router.get("/{apislug}", response_model=GETAPIResponse)
async def get(
    apislug: str = Path(..., min_length=1),
    token: DecodedToken = Depends(get_decoded_token),
):
    api = await apis_db.get(userid=token.sub, apislug=apislug)
    if api is None:
        logger.info(f"{apislug=} not found for user={token.sub}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
    logger.info(f"{apislug=} user={token.sub}")
    return api


class GETAllAPIResponse(ImmutBaseModel):
    apis: list[GETAPIResponse]


@apis_router.get("", response_model=GETAllAPIResponse)
async def get_all(token: DecodedToken = Depends(get_decoded_token)):
    apis = await apis_db.get_all(userid=token.sub)
    logger.info(f"{len(apis.apis)} apis found for user={token.sub}")
    return apis


class POSTAPIRequest(StrictBaseModel):
    description: str = Field(..., min_length=1, max_length=200)


class POSTAPIResponse(ImmutBaseModel):
    apislug: str
    userid: UUID4
    client_secret: str
    description: Optional[str] = None


@apis_router.post("", response_model=POSTAPIResponse)
async def create(
    data: POSTAPIRequest,
    token: DecodedToken = Depends(get_decoded_token),
):
    new_api = await apis_db.create(userid=token.sub, description=data.description)
    if new_api is None:
        logger.log(f"Could not create a new api for user={token.sub} with description='{data.description}'")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unprocessable Entity.",
        )
    logger.info(f"api={new_api.apislug} created for user={token.sub}")
    return new_api


class DELETEAPIResponse(ImmutBaseModel):
    deleted: bool


@apis_router.delete(
    "/{apislug}",
    response_model=DELETEAPIResponse,
    dependencies=[Depends(empty_body)],
)
async def delete(
    apislug: str = Path(..., min_length=1),
    token: DecodedToken = Depends(get_decoded_token),
):
    result = await apis_db.delete(userid=token.sub, apislug=apislug)
    if result is None:
        logger.info(f"Not Found: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if result == APIState.FORZEN:
        logger.info("Frozen can't delete: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource frozen.")
    if result == APIState.UNKNOWN:
        logger.critical(f"Unknown: while deleting {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result == APIState.DELETED:
        logger.info(f"Deleted: {apislug=} for user={token.sub}")
        return {"deleted": True}
    logger.critical(f"Unreachable: APIState={result} while deleting {apislug=} for user={token.sub}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


class POSTToggleResponse(ImmutBaseModel):
    disabled: bool


@apis_router.post(
    "/disable/{apislug}",
    response_model=POSTToggleResponse,
    dependencies=[Depends(empty_body)],
)
async def disable(
    apislug: str = Path(..., min_length=1),
    token: DecodedToken = Depends(get_decoded_token),
):
    result = await apis_db.disable(userid=token.sub, apislug=apislug)
    if result is None:
        logger.info(f"Not Found: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if result == APIState.FORZEN:
        logger.info("Frozen can't disable: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource frozen.")
    if result == APIState.UNKNOWN:
        logger.critical(f"Unknown: while disabling {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result == APIState.DISABLED:
        logger.info(f"Disabled: {apislug=} for user={token.sub}")
        return {"disabled": True}
    logger.critical(f"Unreachable: APIState={result} while disabling {apislug=} for user={token.sub}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@apis_router.post(
    "/enable/{apislug}",
    response_model=POSTToggleResponse,
    dependencies=[Depends(empty_body)],
)
async def enable(
    apislug: str = Path(..., min_length=1),
    token: DecodedToken = Depends(get_decoded_token),
):
    result = await apis_db.enable(userid=token.sub, apislug=apislug)
    if result is None:
        logger.info(f"Not found: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if result == APIState.FORZEN:
        logger.info("Frozen can't enable: {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource frozen.")
    if result == APIState.UNKNOWN:
        logger.critical(f"Unknown: while disabling {apislug=} for user={token.sub}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if result == APIState.ENABLED:
        logger.info(f"Enabled: {apislug=} for user={token.sub}")
        return {"disabled": False}
    logger.critical(f"Unreachable: APIState={result} while enabling {apislug=} for user={token.sub}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


class POSTKeyResponse(ImmutBaseModel):
    apislug: str
    client_secret: str


@apis_router.post(
    "/key/{apislug}",
    response_model=POSTKeyResponse,
    dependencies=[Depends(empty_body)],
)
async def key_change(
    apislug: str = Path(..., min_length=1),
    token: DecodedToken = Depends(get_decoded_token),
):
    client_secret = await apis_db.update_secret(userid=token.sub, apislug=apislug)
    if client_secret is None:
        logger.info(f"Could not issue new client_secret: {apislug=} user={token.sub}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return {"apislug": apislug, "client_secret": client_secret}
