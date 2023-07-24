from sqlalchemy.orm.session import Session
from sqlalchemy import text
from schemas import UserBase, User_Change_Password
from db.models import User
from fastapi import HTTPException, status, Query
from utils.hash import Hash
from db.db_area import get_area
#create user
def create_user(request: UserBase, db: Session):
   
    user = get_user_by_username(request.username,db)
    email = get_user_by_email(request.email,db)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='username đã tồn tại')
    elif email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='email đã tồn tại')
     
    try:
        area_id = get_area(request,db)
        new_user = User(
            USER_NAME = request.username,
            PASSWORD = Hash.bcrypt(request.password),
            FULL_NAME = request.fullname,
            EMAIL = request.email,        
            TEL_NUM = request.telNumber,
            DATE_OF_BIRTH = request.birthday,
            GENDER = request.gender,
            HOME_NUMBER = request.address,
            SIZE_ID = int(request.size_id),
            LINK_FB = request.link_fb,
            ORG_ID = request.org_id,
            AREA_ID = area_id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        #add_role_user(new_user,db)
        response = {
            "status": 200,
            "detail": "Thao tác thành công!"
        }
        return response
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.aaa')


def change_password(user: User_Change_Password, db: Session, current_user: User):
    try:
        authenticate_user(current_user,user.old_password)
        current_user.PASSWORD = Hash.bcrypt(user.new_password)
        
        db.commit()
        response = {
            "status": 200,
            "detail": "Đổi mật khẩu thành công"
        }
        return response
    except :
        db.rollback()
        raise HTTPException(status_code=401, detail="Wrong password")


def authenticate_user(user: User, password: str):
    if not Hash.verify(user.PASSWORD, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password",
        )
    
def get_user_by_username(username: str, db: Session): 
    user = db.query(User).filter(User.USER_NAME == username).first()
    if not user:
        return None
    return user

def get_user_by_email(email: str, db: Session): 
    user = db.query(User).filter(User.EMAIL == email).first()
    if not user:
        return None
    return user

  


    

