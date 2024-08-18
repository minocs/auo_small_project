#fastapi-jwt/main.py
from typing import List
import fastapi as _fastapi
import fastapi.security as _security
 
import sqlalchemy.orm as _orm
 
import services as _services, schemas as _schemas
 
app = _fastapi.FastAPI()
 
@app.post("/token")
async def Login(
    form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(),
    db: _orm.Session = _fastapi.Depends(_services.get_db),
):
    user = await _services.authenticate_user(form_data.username, form_data.password, db)
 
    if not user:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid Credentials")
 
    return await _services.create_token(user)
 
 
@app.get("/users/me", response_model=_schemas.User)
async def Read_Users_Me(user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    return user