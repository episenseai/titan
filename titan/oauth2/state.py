import secrets
import string
from datetime import datetime
from typing import Union

from pydantic import StrictStr

from ..models import ImmutBaseModel
from .models import IdP


class StateToken(ImmutBaseModel):
    state: StrictStr
    # state representing the state of UI, like curren URL before
    # starting the login flow. This can be recovered, once the
    # Login is successfull, by sending the state back to the
    # frontend
    uistate: str
    idp: IdP
    created_at: datetime

    @staticmethod
    def mint(idp: IdP, uistate: str) -> "StateToken":
        alphabet = string.ascii_letters + string.digits
        while True:
            state = "".join(secrets.choice(alphabet) for _ in range(48))
            if (
                sum(c.islower() for c in state) >= 3
                and sum(c.isupper() for c in state) >= 3
                and sum(c.isdigit() for c in state) >= 3
            ):
                break
        token = StateToken(state=state, uistate=uistate, idp=idp.value, created_at=datetime.utcnow())
        return token


class StateTokenDB:
    def __init__(self):
        self.db = {}

    def store(self, token: StateToken):
        self.db[token.state] = token

    def pop_and_verify(self, state: str) -> Union[StateToken, bool]:
        token = self.db.pop(state, None)
        if token:
            if token.created_at < datetime.utcnow():
                return token
        return False
