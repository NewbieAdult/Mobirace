import shutil
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from fastapi import APIRouter
import os


router = APIRouter(
)

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    title: Optional[str] = Form(None)
):
    upload_folder = "mrun_be/images"
    os.makedirs(upload_folder, exist_ok=True)
    # Lưu hình ảnh vào thư mục uploads
    with open(os.path.join(upload_folder, file.filename), "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    saved_file_path = os.path.join(upload_folder, file.filename)

    # Tạo một JSONResponse với các thông tin bạn muốn trả về
    response_data = {
        "name": name,
        "title": title,
        "file_name": file.filename,
        "content_type": file.content_type,
        "saved_file_path": saved_file_path
    }
    
    return JSONResponse(content=response_data)

