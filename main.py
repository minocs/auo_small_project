#fastapi-jwt/main.py
from typing import List
from fastapi import File, UploadFile, Depends, HTTPException
from zipfile import ZipFile
from io import BytesIO
import os
import time
from cryptography.fernet import Fernet
import fastapi as _fastapi
import fastapi.security as _security
import sqlalchemy.orm as _orm
import services as _services, schemas as _schemas, models as _models, database as _database
 
app = _fastapi.FastAPI()

oauth2schema = _security.OAuth2PasswordBearer(tokenUrl="/token")

db =_database.SessionLocal()

# 生成密鑰並創建加密套件
key = Fernet.generate_key()
cipher_suite = Fernet(key)

"""
@app.post("/users/new")
async def create_user(
    user: _schemas.UserCreate, db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    db_user = await _services.get_user_info(user.user_name, db)
    if db_user:
        raise _fastapi.HTTPException(status_code=400, detail="user_name already in use")
 
    user = await _services.create_user(user, db)
 
    return await _services.create_token(user)
"""
     
@app.post("/token")
async def Login(
    form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(),
    db: _orm.Session = _fastapi.Depends(_services.get_db),
):
    user = await _services.authenticate_user(form_data.username, form_data.password, db)

    user_id = user
 
    if not user:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid Credentials")
 
    return await _services.create_token(user)
 
""" 
@app.get("/users/me", response_model=_schemas.User)
async def Read_Users_Me(user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    return user
"""

def verify_token(token: str = Depends(oauth2schema)):
    # 這裡會執行 JWT 驗證邏輯
    return {"sub": "user"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    token: dict = Depends(verify_token),
    current_user: _models.User = Depends(_services.get_current_user),
):
    # 檢查是否為 zip 檔案
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zip archive.")
    
    # 解壓縮並檢查內容
    contents = await file.read()
    with ZipFile(BytesIO(contents)) as zip_file:
            
        # 預設訊息    
        _msg = 'No error'
        _valid_status = 'success'    

        # 獲取壓縮檔內的文件名列表，過濾掉 __MACOSX 目錄
        files_in_zip = [f for f in zip_file.namelist() if not f.startswith('__MACOSX/')]
        
        # 檢查文件數量和名稱
        allowed_files = {'A.txt', 'B.txt', 'C.txt'}
        
        # 過濾出壓縮包中根目錄的文件（排除可能存在的子目錄文件）
        root_files = {os.path.basename(name) for name in files_in_zip if not name.endswith('/')}
        
        # 檢查是否包含必須的 A.txt 和 B.txt
        if 'A.txt' not in root_files or 'B.txt' not in root_files:
            _msg = "Zip file must contain A.txt and B.txt."
            _valid_status = 'fail'
            #raise HTTPException(status_code=400, detail=_msg)
        
        # 確認只有允許的文件
        elif not root_files.issubset(allowed_files):
            _msg = "Zip file contains invalid files."
            _valid_status = 'fail'
            #raise HTTPException(status_code=400, detail=_msg)

        # 設定存儲路徑並創建資料夾
        upload_dir = "uploads"
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Could not create upload directory: {e}")

        
        # 生成唯一的文件名，添加時間戳記
        timestamp = time.strftime("%Y%m%d%H%M%S")
        zip_filename = f"{os.path.splitext(file.filename)[0]}_{timestamp}.zip"
        save_path = os.path.join(upload_dir, zip_filename)
        
        # 加密檔案內容
        encrypted_contents = cipher_suite.encrypt(contents)
        
        # 保存加密後的 zip 檔案
        with open(save_path, "wb") as f:
            f.write(encrypted_contents)        
        
        # 寫入 file table
        file_obj = _models.File(
            file_name = zip_filename,
            valid_status = _valid_status,
            encryption_key = key,
            error_msg = _msg,
            created_dt = time.strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(file_obj)
        db.commit() 
        db.refresh(file_obj)  

        _user_id = current_user.id        
        
        # 寫入 upload table
        upload_obj = _models.Upload(
            user_id = _user_id,
            file_id = file_obj.id,
            created_dt = time.strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(upload_obj)
        db.commit()
        db.refresh(upload_obj) 
        
    return {"valid status": _valid_status, "message": _msg, "filename": zip_filename}



@app.get("/upload_records", response_model=List[_schemas.UploadRecord])
async def get_upload_records(
    db: _orm.Session = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
    ):
    
    try:
        # 查詢 Upload 表，並與 User 表和 File 表聯結
        results = db.query(
            _models.User.user_name,
            _models.File.file_name,
            _models.File.valid_status,
            _models.Upload.created_dt
        ).join(
            _models.File, _models.Upload.file_id == _models.File.id
        ).join(
            _models.User, _models.Upload.user_id == _models.User.id
        ).all()
        
        # 將查詢結果轉換為 jason format
        records = [
            {
                "user_name": result[0],
                "file_name": result[1],
                "valid_status": result[2],
                "created_dt": result[3]
            }
            for result in results
        ]
        
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
