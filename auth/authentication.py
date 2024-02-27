#25/7/2023
#Nguyen Sinh Hung
from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from db.database import get_db
from auth import oauth2
from utils.hash import Hash
from jose import jwt
from jose.exceptions import JWTError
from db.db_function import get_api_path_hierarchy
from db.db_user import get_user_by_username
from schemas import RefreshTokenRequest
from auth.oauth2 import get_user_google,get_facebook_user_info, check_ldap_user
from db.db_role import get_roleId_by_user
from schemas import AuthLoginThird
from lib.get_hierarchical_data import hierarchical_data, Argument
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
    roleId = get_roleId_by_user(user, db)
    if not user or not Hash.verify(user.PASSWORD, request.password):
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    funcId = [3,4] if roleId == 1 else [4]
    path_api = get_api_path_hierarchy(funcId,roleId, db)
#SINH HUNG 31/07/2023
    listPath = hierarchical_data(path_api, Argument(keyAtrrName='FUNC_ID',
                                                    parentAtrrName='FUNC_PARENT_ID',                                                    
                                                    labelAtrrName='FUNC_NAME',
                                                    pathAtrrName='API_PATH',
                                                    iconAtrrName='ICON'
                                                    ))
    
    access_token = oauth2.create_access_token(data={'sub': user.USER_NAME})
    refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME})
    
    return {
    'accessToken': access_token,
    'refreshToken': refresh_token,
    'username': user.USER_NAME,
    'fullName': user.FULL_NAME,
    'acceptUrl': listPath,
    'roleId' : roleId,
    'userId': user.USER_ID
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
    roleId = get_roleId_by_user(user, db)
    if not user:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token has expired or invalid")
    funcId = [3,4] if roleId == 1 else [4]
    path_api = get_api_path_hierarchy(funcId,roleId, db)
#SINH HUNG 31/07/2023
    listPath = hierarchical_data(path_api, Argument(keyAtrrName='FUNC_ID',
                                                    parentAtrrName='FUNC_PARENT_ID',                                                    
                                                    labelAtrrName='FUNC_NAME',
                                                    pathAtrrName='API_PATH',
                                                    iconAtrrName='ICON'
                                                    ))
    access_token = oauth2.create_access_token(data={'sub': user.USER_NAME})
    refresh_token = oauth2.create_refresh_token(data={'sub': user.USER_NAME})
    return {
    'accessToken': access_token,
    'refreshToken': refresh_token,
    'username': user.USER_NAME,
    'fullName': user.FULL_NAME,
    'acceptUrl': listPath,
    'roleId' : roleId,
    'userId': user.USER_ID
}
  except JWTError:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Refresh token has expired or invalid')
  
@router.post('/login/third-party')
async def login_google(request: AuthLoginThird, db: Session = Depends(get_db)):
  try: 
    if request.type == '1':
      return await get_user_google(request.accessToken, db)
    if request.type == '2':
      return get_facebook_user_info(request.accessToken, db)
  except:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
      detail=f'Authorization failed')

# API đăng nhập LDAP tung.nguyenson11 28/08/2023 
@router.post('/login/mobifone')
def login_ldap(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
  try:
    username = request.username.replace("@mobifone.vn","")
    password = request.password
    result = check_ldap_user(username, password, db)
    return result
  except JWTError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Refresh token has expired or invalid')

  


 