import secrets
import string
from datetime import datetime
from typing import Optional, Union

from pydantic import StrictStr

from ..utils import ImmutBaseModel
from .idp import IDP


class StateToken(ImmutBaseModel):
    # `state` is there to protect the end user from cross site r
    # equest forgery(CSRF) attacks. It is introduced from OAuth 2.0
    # protocol
    # https://tools.ietf.org/html/rfc6749#section-10.12
    state: StrictStr
    # `nonce` binds the token with the client. So the client can validate
    # the token it received against the initial authorization request,
    # thus ensuring the validity of the token. Prevents replay attacks.
    # https://openid.net/specs/openid-connect-core-1_0.html#CodeFlowSteps
    nonce: Optional[StrictStr] = None
    # `uistate` represents the state of UI, like curren URL before
    # starting the login flow. This can be recovered, once the
    # Login is successfull, by sending the state back to the
    # frontend.
    uistate: Optional[str] = None
    idp: IDP
    created_at: datetime

    @staticmethod
    def gen_state(num_bytes: int = 48) -> str:
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
    def mint(cls, idp: IDP, uistate: Optional[str] = None, with_nonce: bool = False) -> "StateToken":
        state = cls.gen_state()
        if with_nonce:
            nonce = cls.gen_state()
        else:
            nonce = None
        token = StateToken(
            state=state,
            nonce=nonce,
            uistate=uistate,
            idp=idp.value,
            created_at=datetime.utcnow(),
        )
        return token


class StateTokensDB:
    def __init__(self):
        self.db = {}

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    def store(self, token: StateToken):
        self.db[token.state] = token

    def pop_and_verify(self, state: str) -> Union[StateToken, bool]:
        token = self.db.pop(state, None)
        if token:
            if token.created_at < datetime.utcnow():
                return token
        return False
