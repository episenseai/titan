import secrets
import string
from datetime import timedelta
from typing import Optional, Union

import redis
from pydantic import UUID4

from ..logger import logger
from ..utils import ImmutBaseModel
from .idp import IdentityProvider


class StateToken(ImmutBaseModel):
    # `state` is there to protect the end user from cross site r
    # equest forgery(CSRF) attacks. It is introduced from OAuth 2.0
    # protocol
    # https://tools.ietf.org/html/rfc6749#section-10.12
    state: str
    # `nonce` binds the token with the client. So the client can validate
    # the token it received against the initial authorization request,
    # thus ensuring the validity of the token. Prevents replay attacks.
    # https://openid.net/specs/openid-connect-core-1_0.html#CodeFlowSteps
    nonce: str = ""
    # `uistate` represents the state of UI, like curren URL before
    # starting the login flow. This can be recovered, once the
    # Login is successfull, by sending the state back to the
    # frontend.
    ustate: UUID4
    idp: IdentityProvider

    @staticmethod
    def gen_state(num_bytes: int = 64) -> str:
        if num_bytes < 18:
            raise ValueError(f"{num_bytes=} in random state token is too small")
        alphabet = string.ascii_letters + string.digits
        while True:
            state = "".join(secrets.choice(alphabet) for _ in range(num_bytes))
            if (
                sum(c.islower() for c in state) >= 3
                and sum(c.isupper() for c in state) >= 3
                and sum(c.isdigit() for c in state) >= 3
            ):
                break
        return state

    @classmethod
    def issue(cls, idp: IdentityProvider, ustate: UUID4, with_nonce: bool = False) -> "StateToken":
        state = cls.gen_state()
        if with_nonce:
            nonce = cls.gen_state()
        else:
            nonce = ""
        token = StateToken(
            state=state,
            nonce=nonce,
            ustate=ustate,
            idp=idp.value,
        )
        return token


class StateTokensDB:
    def __init__(
        self, redis_host: str, redis_port: int, redis_password: Optional[str], redis_db: int
    ):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, password=redis_password, db=redis_db
        )
        self.expire_delta = timedelta(minutes=8)

    def store(self, token: StateToken):
        self.redis.set(
            name=token.state,
            value=token.json(),
            ex=self.expire_delta,
        )

    def pop_and_verify(self, state: str) -> Union[StateToken, bool]:
        result = self.redis.execute_command("GETDEL", state)
        if not result:
            return False
        try:
            token = StateToken.parse_raw(result)
            return token
        except Exception as exc:
            logger.exception(f"Error decoding StateToken from redis: {exc}")
            return False
