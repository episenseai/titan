from pydantic import BaseModel


class ImmutBaseModel(BaseModel):
    class Config:
        # faux immutability of fields
        allow_mutation = False
        # validate field defaults
        validate_all = True


class AssignValidateBaseModel(BaseModel):
    class Config:
        # whether to perform validation on assignment to attributes
        validate_assignment = True
