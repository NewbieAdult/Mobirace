from fastapi import APIRouter, File, UploadFile, HTTPException
import shutil
import os

router = APIRouter(
    prefix='/picture',
    tags=['picture']
)

MAX_FILE_SIZE_MB = 1

@router.post('/file')
def get_picture(file: bytes = File(...)):
    content = file.decode('utf-8')
    lines = content.split('\n')
    return {'lines': lines}

@router.post('/uploadfile')
def uploadfile(upload_file: UploadFile = File(...)):
    # Kiểm tra kích thước của tệp
    file_size_mb = upload_file.file.seek(0, os.SEEK_END)
    file_size_mb /= (1024 * 1024)
    upload_file.file.seek(0) 

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File size exceeds the allowed limit (1MB).")

    path = f"files/{upload_file.filename}"
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return {
        'filename': path,
        'type': upload_file.content_type
    }
