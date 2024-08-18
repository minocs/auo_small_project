#fastapi-jwt/schemas.py
import datetime as _dt
 
import pydantic as _pydantic
 
class _UserBase(_pydantic.BaseModel):
    user_name: str

    class Config:
        from_attributes = True
 
class UserCreate(_UserBase):
    password: str
    
    class Config:
        orm_mode = True
 
class User(_UserBase):
    id: int
 
    class Config:
        orm_mode = True