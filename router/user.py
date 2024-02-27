#25/7/2023
#Nguyen Sinh Hung
from schemas import UserBase, User_Change_Password, User_Reset_Password, UserDisplay
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_user
from db.db_user import create_user
from db.models import User
from auth.oauth2 import get_current_user
from utils import validation
from utils.hash import Hash
from typing import Optional, Union
from utils.base_url import get_base_url
from datetime import datetime
router = APIRouter(
  prefix='/user',
  tags=['user'] 
)

# Create user
@router.post('/register')
async def register_user(request: UserBase, db: Session = Depends(get_db)):
  if not request.username or not request.email:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Tài khoản hoặc email không hợp lệ. Vui lòng nhập lại!')
  if request.telNumber!=None:
      number = validation.is_valid_phone(request.telNumber)
      if number == False:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Số điện thoại không hợp lệ. Vui lòng nhập lại!')
  #NGUYEN SINH HUNG 27/7/2023
  #ACCOUNT GOOGLE
  if request.email == request.username:
     username = validation.is_valid_email(request.username)
     email = validation.is_valid_email(request.email)
     if username == False or email == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'Tài khoản hoặc email không hợp lệ. Vui lòng nhập lại!')
     if request.password :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'Mật khẩu chưa chính xác. vui lòng nhập lại!')
     request.type_account = '1'
     
  #ACCOUNT FACEBOOK
  elif validation.contains_username_fb(request.username):
    if request.password :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'Mật khẩu chưa chính xác. vui lòng nhập lại!')
    request.type_account = '2'
   #ACCOUNT MOBIFONE
  elif request.email.endswith('@mobifone.vn'):
    email = validation.is_valid_email(request.email)
    username = validation.is_valid_username(request.username)
    if username == False or email == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'Tài khoản hoặc email không hợp lệ. Vui lòng nhập lại!')
    request.type_account = '3'
  else:
    #ACCOUNT LOCAL
    if not request.password:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Vui lòng nhập mật khẩu!')
    email = validation.is_valid_email(request.email)
    username = validation.is_valid_username(request.username)
    if username == False or email == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'Tài khoản hoặc email không hợp lệ. Vui lòng nhập lại!')
    request.password=Hash.bcrypt(request.password)
  return await create_user(request, db)

#Change Password
@router.put('/change-password')
def change_password(request: User_Change_Password, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
  return db_user.change_password(request, db, current_user)

#Reset Password
@router.put('/reset-password')
def reset_password(request: User_Reset_Password, db: Session = Depends(get_db), host: str = Depends(get_base_url)):
  email = validation.is_valid_email(request.email)
  username = validation.is_valid_username(request.username)
  if username == False :
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Tài khoản không hợp lệ!')
  if email == False :
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Email không hợp lệ!')
  # return db_user.reset_password(request, db)
  return db_user.reset_password_user(request, db, host)

#Update 
@router.put('/update')
def update_user(fullname: str =Form(None), 
                email: Optional[str] =Form(None) ,
                telNumber: Optional[str] =Form(None),
                birthday: datetime=Form(None),
                gender: Optional[str] =Form(None),
                address: Optional[str]=Form(None),
                province: Optional[str]=Form(None),
                district: Optional[str]=Form(None),
                ward: Optional[str]=Form(None), 
                org_id:  Union[int, str] =Form(None),
                child_org_id:  Union[int, str] =Form(None),
                size_id: Union[int, str] =Form(None),
                link_fb: Optional[str]=Form(None),
                image: Union[UploadFile,str] = Form(None),db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
  if current_user.TYPE_ACCOUNT==1:
    if email:
     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Email không hợp lệ!')
  return db_user.update_user( db, current_user,
                              fullname=fullname, 
                              email=email,
                              telNumber=telNumber,
                              birthday=birthday,
                              gender=gender,
                              address=address,
                              province=province,
                              district=district,
                              ward=ward,
                              org_id=org_id,
                              child_org_id=child_org_id,
                              size_id=size_id,
                              link_fb=link_fb,
                              image=image )

# Read one user
@router.get('/', response_model=UserDisplay)
def get_infor_user(current_user: User = Depends(get_current_user), host: str = Depends(get_base_url)):
  area = current_user.area
  image_path = current_user.AVATAR_PATH.replace("\\", "/")
  user_display = UserDisplay(
        fullname=current_user.FULL_NAME,
        email=current_user.EMAIL,
        telNumber=current_user.TEL_NUM,
        birthday=str(current_user.DATE_OF_BIRTH),
        gender=current_user.GENDER,
        address=current_user.HOME_NUMBER,
        org_id=current_user.ORG_ID,
        child_org_id=current_user.ORG_CHILD_ID,
        size_id=current_user.SIZE_ID,
        link_fb=current_user.LINK_FB,
        image=f"{host}/{image_path}",
    )
  if area:
    user_display.province = area.PROVINCE if area.PROVINCE is not None else None
    user_display.district = area.DISTRICT if area.DISTRICT is not None else None
    user_display.ward = area.PRECINCT if area.PRECINCT is not None else None
  return user_display 




    
