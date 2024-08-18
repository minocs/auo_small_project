#fastapi-jwt/models.py
import datetime as _dt
 
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash
 
import database as _database
 
class User(_database.Base):
    __tablename__ = "user"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_name = _sql.Column(_sql.String, unique=True, index=True)
    password = _sql.Column(_sql.String)
 
    def verify_password(self, password_: str):
        return _hash.bcrypt.verify(password_, self.password)