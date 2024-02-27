#25/7/2023
#Nguyen Sinh Hung
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_user
from db.models import User
from auth.oauth2 import get_current_user
from utils.strava import revoke_access_token

router = APIRouter(
  prefix='/strava',
  tags=['strava']
)

@router.post('/authorize-code')
def exchange_authorization_code(authorizecode: str, db: Session = Depends(get_db), 
                                current_user: User = Depends(get_current_user)):          
  return db_user.add_info_strava(authorizecode, db, current_user)

@router.post('/disconnect')
def disconnect(db: Session = Depends(get_db), 
                                current_user: User = Depends(get_current_user)):
  return revoke_access_token(db, current_user)

@router.get('/get-info')
def get_strava_info(db: Session = Depends(get_db), 
                                current_user: User = Depends(get_current_user)):          
  return db_user.get_info_user_strava(db, current_user)
