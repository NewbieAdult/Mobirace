from typing import List
from schemas import UserBase, User_Change_Password
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_user
from db.models import User
from auth.oauth2 import get_current_user
from fastapi import HTTPException, status
from utils import validation
router = APIRouter(
  prefix='/user',
  tags=['user']
)

# Create user
@router.post('/register')
def create_user(request: UserBase, db: Session = Depends(get_db)):
  if not request.username:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Name is required')
  email = validation.is_valid_email(request.email)
  username = validation.is_valid_username(request.username)
  if username == False :
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Username invalid')
  if email == False :
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'Email invalid')
  if request.telNumber!=None:
    number = validation.is_valid_phone(request.telNumber)
    if number == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
          detail=f'phone number invalid')
  return db_user.create_user(request, db)

#Change Password
@router.put('/change-password')
def change_password(request: User_Change_Password, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
  return db_user.change_password(request, db, current_user)

