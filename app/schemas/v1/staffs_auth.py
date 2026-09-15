from pydantic import BaseModel, Field


class StaffLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=6)


class StaffRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: str
    password: str = Field(..., min_length=6)
    business_name: str = Field(..., min_length=2, max_length=255)


class StaffAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
