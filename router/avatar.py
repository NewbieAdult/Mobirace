from fastapi import FastAPI,APIRouter, UploadFile, File, HTTPException,status
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from db.database import declarative_base,SessionLocal
from db.models import User
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Response, Body, BackgroundTasks, APIRouter
import base64
from fastapi.templating import Jinja2Templates
import requests
router=APIRouter(
    prefix='/pic',
    tags=['pic']
)
avatar_images_directory = "C:/Users/Admin/Pictures"
router.mount("/avatar_images", StaticFiles(), name="avatar_images")
@router.post("/upload_avatar/")
async def upload_avatar(avatar: UploadFile = File(...)):
    # Kiểm tra kích thước ảnh
    if avatar.size > 1024 * 1024:  # Giới hạn dung lượng tệp là 1MB
        raise HTTPException(
            status_code=400,
            detail="Kích thước tệp ảnh không được vượt quá 1MB."
        )

    # Lưu binary code của ảnh vào cơ sở dữ liệu
    try:       
        with SessionLocal() as db:
            user = User(AVATAR_PATH=avatar.file.read())
            db.add(user)
            db.commit()
            return {"message": "Avatar đã được tải lên và lưu vào cơ sở dữ liệu thành công."}
    except:
        raise HTTPException(status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,detail="kich thuoc vuot qua gioi han")
@router.get("/view_avatar/{user_id}")
async def view_avatar(request: Request, user_id: int):
    # Lấy binary code của ảnh từ cơ sở dữ liệu
    with SessionLocal() as db:
        user = db.query(User).filter(User.USER_ID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại.")
        avatar_binary = user.AVATAR_PATH

    # Giải mã binary code thành dữ liệu ảnh
    avatar_image = base64.b64encode(avatar_binary).decode("utf-8")

    # Trả về hiển thị ảnh
    return avatar_image