import secrets
import string
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qsl, urlencode
from uuid import uuid4

import httpx
from devtools import debug
from fastapi import APIRouter, Query, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from pydantic import AnyHttpUrl, StrictStr, validator

from ..model import ImmutBaseModel
from ..tokens.jwt import AccessRefreshToken, TokenClaims

github_router = APIRouter()

APP_URL = "http://localhost:8000"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

GITHUB_REDIRECT_URL = f"{APP_URL}/auth/github"
GITHUB_SCOPES = "user:email"
GITHUB_CLIENT_ID = "5ffe8fd42976c5f477e3"

GITHUB_CLIENT_SECRET = "d6d6dc23b03f3b53a3d471ae02acd76c3e893ded"

GITHUB_USER_URL = "https://api.github.com/user"

GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "WmUcqKFLcbiYSqghIIuUi4Hb"


class StateTokenDB:
    def __init__(self):
        self.db = {}

    def get(self, state: str):
        return self.db.get(state, None)

    def store(self, state: str, provider: str):
        self.db[state] = {"created": datetime.utcnow(), "provider": provider}

    def verified(self, state: str) -> bool:
        val = self.get(state)
        if val:
            if val["created"] < datetime.utcnow():
                return True
        return False


state_token_db = StateTokenDB()


class AuthURLParams(ImmutBaseModel):
    client_id: str
    redirect_uri: AnyHttpUrl
    scope: str
    state: str

    def urlencode(self):
        return urlencode(self.dict())


class Oauth2StateToken(ImmutBaseModel):
    state: Optional[StrictStr] = None

    @validator("state", pre=True)
    def generate_state_token(cls, v):
        if isinstance(v, str):
            return v
        alphabet = string.ascii_letters + string.digits
        while True:
            state = "".join(secrets.choice(alphabet) for _ in range(24))
            if (
                sum(c.islower() for c in state) >= 3
                and sum(c.isupper() for c in state) >= 3
                and sum(c.isdigit() for c in state) >= 3
            ):
                break
        return state

    def generate_auth_url_params(self, client_id: str, redirect_uri: AnyHttpUrl, scope: str) -> AuthURLParams:
        return AuthURLParams(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=GITHUB_SCOPES,
            state=self.state,
        )


@github_router.get("/login")
async def auth_url_redirect():
    try:
        state = Oauth2StateToken()
        url_params = state.generate_auth_url_params(
            client_id=GITHUB_CLIENT_ID, redirect_uri=GITHUB_REDIRECT_URL, scope=GITHUB_SCOPES
        )
        encoded_params = url_params.urlencode()
        auth_url = f"{GITHUB_AUTH_URL}?{encoded_params}"
        debug(url_params, encoded_params, auth_url)
        state_token_db.store(state.state, GITHUB_AUTH_URL)
    except Exception as ex:
        print(ex)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Request",
        )

    return RedirectResponse(auth_url)


class Token(ImmutBaseModel):
    access_token: str
    token_type: str


class AccessTokenURLParams(ImmutBaseModel):
    client_id: str
    client_secret: str
    code: str
    state: str

    def urlencode(self):
        return urlencode(self.dict())


class UserDB:
    def __init__(self):
        self.db = {}

    def get(self, email: str):
        return self.db.get(email, None)

    def store(self, username: str, data: dict):
        self.db[username] = data


user_db = UserDB()


@github_router.get("/auth/github", response_model=AccessRefreshToken)
async def auth_callback(request: Request, code: Optional[str] = Query(None), state: Optional[str] = Query(None)):
    auth_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Authorization Failed",
    )

    # should not contain more then 2 params in callback
    if not code or not state or len(request.query_params) > 2:
        raise auth_error

    # if not state_token_db.verified(state):
    # raise auth_error
    try:
        url_params = AccessTokenURLParams(
            client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET, code=code, state=state
        )
        debug(url_params)
        async with httpx.AsyncClient() as client:
            token_response = await client.post(GITHUB_TOKEN_URL, params=url_params.dict())
            decoded_form = token_response.content.decode()
            debug(token_response, token_response.status_code, decoded_form)

            # check X-rate-limit error

            response_dict = dict(parse_qsl(decoded_form))
            debug(response_dict)
            github_access_token = response_dict.get("access_token", None)
            github_ttype = response_dict.get("token_type", None)
            if github_access_token is None:
                raise ValueError("Can not get access token from github")
            if github_ttype.lower() != "bearer":
                raise ValueError("token_type error from github")
            github_header = {"Authorization": f"token {github_access_token}"}
            debug(github_access_token, github_header)

            user_response = await client.get(GITHUB_USER_URL, headers=github_header)
            debug(user_response.headers, user_response.text, user_response.encoding)
            github_user = user_response.json()
            debug(github_user)

        user = user_db.get(github_user["login"])
        if user is None:
            github_user["uuid"] = str(uuid4())
            github_user["scopes"] = "episense:demo"
            user_db.store(github_user["login"], github_user)
            user = user_db.get(github_user["login"])
        debug(user)
        # email might not be prsent if the user has marked it as private
        # maybe redirect here to owr own url to get other user info and then
        # issue tokens

        token_claims = TokenClaims(sub=user["uuid"], scopes=user["scopes"])
        token = token_claims.mint_access_refresh_token()
        debug(token)
        return token
    except Exception as ex:
        import traceback

        traceback.print_exc()
        print(ex)
        raise auth_error
