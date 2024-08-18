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
    
class File(_database.Base):
    __tablename__ = "file"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    file_name = _sql.Column(_sql.String)
    valid_status = _sql.Column(_sql.String)
    encryption_key = _sql.Column(_sql.String)
    error_msg = _sql.Column(_sql.String)
    created_dt = _sql.Column(_sql.String)

class Upload(_database.Base):
    __tablename__ = "upload"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer)
    file_id = _sql.Column(_sql.Integer)
    created_dt = _sql.Column(_sql.String)