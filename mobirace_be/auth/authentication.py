from fastapi import APIRouter, HTTPException, status, Body
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from db.database import get_db
from auth import oauth2
from utils.hash import Hash
from jose import jwt
from jose.exceptions import JWTError
from db.db_role import get_role_by_userID
from db.db_function import get_func_by_roleID
from db.db_user import get_user_by_username
from schemas import RefreshTokenRequest


router = APIRouter(
  prefix='/auth',
  tags=['authentication']
)

@router.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
  try:
    connection = db.connection().connection
    cursor = connection.cursor()
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Cannot connect to database.')

  try:
    user = get_user_by_username(request.username, db)
    if not user or not Hash.verify(user.PASSWORD, request.password):
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    #user_role = get_role_by_userID(user, db)
    #result = get_func_by_roleID(user_role, db)
    access_token = oauth2.create_access_token(data={'sub': user.USER_NAME})
    refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME})
    #access_token = oauth2.create_access_token(data={'sub': user.USER_NAME, 'role_id': user_role.ROLE_ID })
    #refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME, 'role_id': user_role.ROLE_ID})

    return {
    'accessToken': access_token,
    'refreshToken': refresh_token,
    'username': user.USER_NAME,
    'fullName': user.FULL_NAME,
    'acceptUrl': [
      #func.API_PATH
      #for func in result
    ]
}
  except JWTError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Refresh token has expired or invalid')
  finally:
    cursor.close()
    connection.close()
  


@router.post('/refresh-token')
def refresh_token(request_body: RefreshTokenRequest , db: Session = Depends(get_db)):
  try: 
    payload = jwt.decode(request_body.refresh_Token, oauth2.SECRET_KEY_ACCESS, algorithms=[oauth2.ALGORITHM])
    username: str = payload.get("sub")
    user = get_user_by_username(username, db)
    if not user:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token has expired or invalid")
    #user_role = get_role_by_userID(user, db)
    #result = get_func_by_roleID(user_role, db)

    access_token = oauth2.create_access_token(data={'sub': user.USER_NAME})
    refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME})
    #access_token = oauth2.create_access_token(data={'sub': user.USER_NAME})
    #refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME, 'role_id': user_role.ROLE_ID})

    return {
    'accessToken': access_token,
    'refreshToken': refresh_token,
    'username': user.USER_NAME,
    'fullName': user.FULL_NAME,
    'acceptUrl': [
      #func.API_PATH
      #for func in result
    ]
    }
  except JWTError:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Refresh token has expired or invalid')
  

  
  


 