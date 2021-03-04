import secrets
import string
from datetime import datetime
from typing import Union

from pydantic import StrictStr

from ..model import ImmutBaseModel
from .idp import IdP


class StateToken(ImmutBaseModel):
    state: StrictStr
    provider: IdP
    created_at: datetime

    @staticmethod
    def mint(provider: IdP) -> "StateToken":
        alphabet = string.ascii_letters + string.digits
        while True:
            state = "".join(secrets.choice(alphabet) for _ in range(48))
            if (
                sum(c.islower() for c in state) >= 3
                and sum(c.isupper() for c in state) >= 3
                and sum(c.isdigit() for c in state) >= 3
            ):
                break
        token = StateToken(state=state, provider=provider.value, created_at=datetime.utcnow())
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
