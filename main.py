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
import services as _services, schemas as _schemas, models as _models
 
app = _fastapi.FastAPI()

oauth2schema = _security.OAuth2PasswordBearer(tokenUrl="/token")

user_id = ''

# 生成密鑰並創建加密套件
key = Fernet.generate_key()
cipher_suite = Fernet(key)



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
 
 
@app.get("/users/me", response_model=_schemas.User)
async def Read_Users_Me(user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    return user


def verify_token(token: str = Depends(oauth2schema)):
    # 這裡會執行 JWT 驗證邏輯
    return {"sub": "user"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    token: dict = Depends(verify_token),
):
    # 檢查是否為 zip 檔案
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zip archive.")
    
    # 解壓縮並檢查內容
    contents = await file.read()
    with ZipFile(BytesIO(contents)) as zip_file:
        # 獲取壓縮檔內的文件名列表，過濾掉 __MACOSX 目錄
        files_in_zip = [f for f in zip_file.namelist() if not f.startswith('__MACOSX/')]

       # 設定存儲路徑並創建資料夾
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一的文件名，添加時間戳記
        timestamp = time.strftime("%Y%m%d%H%M%S")
        zip_filename = f"{os.path.splitext(file.filename)[0]}_{timestamp}.zip"
        save_path = os.path.join(upload_dir, zip_filename)
        
        # 加密檔案內容
        encrypted_contents = cipher_suite.encrypt(contents)
        
        # 保存加密後的 zip 檔案
        with open(save_path, "wb") as f:
            f.write(encrypted_contents)        
        
        # 檢查文件數量和名稱
        allowed_files = {'A.txt', 'B.txt', 'C.txt'}
        
        # 過濾出壓縮包中根目錄的文件（排除可能存在的子目錄文件）
        root_files = {os.path.basename(name) for name in files_in_zip if not name.endswith('/')}
        
        # 檢查是否包含必須的 A.txt 和 B.txt
        if 'A.txt' not in root_files or 'B.txt' not in root_files:
            raise HTTPException(status_code=400, detail="Zip file must contain A.txt and B.txt.")
        
        # 確認只有允許的文件
        if not root_files.issubset(allowed_files):
            raise HTTPException(status_code=400, detail="Zip file contains invalid files.")
        
 
        
    return {"message": "Files successfully uploaded, validated, and encrypted.", "filename": zip_filename}
