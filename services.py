#fastapi-jwt/services.py
import fastapi as _fastapi
import fastapi.security as _security
import jwt as _jwt #pip install python_jwt https://pypi.org/project/python-jwt/
import datetime as _dt
import sqlalchemy.orm as _orm
import passlib.hash as _hash
 
import database as _database, models as _models, schemas as _schemas
 
oauth2schema = _security.OAuth2PasswordBearer(tokenUrl="/token")
 
JWT_SECRET = "sean@auosmallproject"
 
def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)
 
def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
async def get_user_info(user_name: str, db: _orm.Session):
    return db.query(_models.User).filter(_models.User.user_name == user_name).first()
 
async def create_user(user: _schemas.UserCreate, db: _orm.Session):
    user_obj = _models.User(
        user_name=user.user_name, password=_hash.bcrypt.hash(user.password)
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj
 
async def authenticate_user(user_name: str, password: str, db: _orm.Session):
    user = await get_user_info(db=db, user_name=user_name)
 
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user
 
 
async def create_token(user: _models.User):
    user_obj = _schemas.User.from_orm(user)
 
    token = _jwt.encode(user_obj.dict(), JWT_SECRET)
 
    return dict(access_token=token, token_type="bearer")
 
async def get_current_user(
    db: _orm.Session = _fastapi.Depends(get_db),
    token: str = _fastapi.Depends(oauth2schema),
):
    try:
        payload = _jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Username or Password"
        )
 
    return _schemas.User.from_orm(user)
