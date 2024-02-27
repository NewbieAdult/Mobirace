#25/7/2023
#Nguyen Sinh Hung
from sqlalchemy.orm.session import Session
from schemas import UserBase
from db.models import User
from fastapi import HTTPException, status, Query
from utils.hash import Hash
from db.models import User, User_Role, Function,Role



def get_roleId_by_user(user: User, db: Session): 
    try:
        roleId = db.query(User_Role.ROLE_ID).join(User, User_Role.USER_ID == User.USER_ID).filter(User.USER_ID == user.USER_ID).first()
        return roleId[0]
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.')

  


    

