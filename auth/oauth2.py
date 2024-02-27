#25/7/2023
#Nguyen Sinh Hung
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.orm import Session
from db.database import get_db
from fastapi import HTTPException, status
from db import db_user
import httpx, os, requests
from db.db_function import get_api_path_hierarchy
from lib.get_hierarchical_data import hierarchical_data, Argument
from db.db_role import get_roleId_by_user
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL 
from db.models import User
from dotenv import load_dotenv
load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY_ACCESS = os.getenv("SECRET_KEY_ACCESS")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESS_TOKEN_EXPIRE_MINUTES"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
  to_encode.update({'iat': datetime.utcnow(), 'exp': expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ACCESS, algorithm=ALGORITHM)
  return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(REFRESS_TOKEN_EXPIRE_MINUTES)
  to_encode.update({'iat': datetime.utcnow(), 'exp': expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ACCESS, algorithm=ALGORITHM)
  return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Could not validate credentials',
      headers={"WWW-Authenticate": "Bearer"}
    )
    try:
      payload = jwt.decode(token, SECRET_KEY_ACCESS, algorithms=[ALGORITHM])
      username: str = payload.get("sub")
      if username is None:
        raise credentials_exception
    except JWTError:
      raise credentials_exception

    user = db_user.get_user_by_username(username, db)

    if user is None:
      raise credentials_exception
    return user

async def get_user_google(access_token_gg: str, db: Session):
    # Make a GET request to the Google OAuth 2.0 endpoint with the access token as a query parameter
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token_gg}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            user_info = response.json()
            #return {"status": "success", "data": user_info}
            if user_info.get('verified_email'):
              email = user_info.get('email')
              user = db_user.get_user_by_username(email, db)
              
              if user and user.TYPE_ACCOUNT == '1':
                  roleId = get_roleId_by_user(user, db)
                  funcId = [3,4] if roleId == 1 else [4]
                  path_api = get_api_path_hierarchy(funcId,roleId, db)
              #SINH HUNG 31/07/2023
                  listPath = hierarchical_data(path_api, Argument(keyAtrrName='FUNC_ID',
                                                                  parentAtrrName='FUNC_PARENT_ID',                                                    
                                                                  labelAtrrName='FUNC_NAME',
                                                                  pathAtrrName='API_PATH',
                                                                  iconAtrrName='ICON'
                                                                  ))
                  access_token = create_access_token(data={'sub': user.USER_NAME})
                  refresh_token = create_refresh_token(data={'sub': user.USER_NAME})
                  return {
                    'accessToken': access_token,
                    'refreshToken': refresh_token,
                    'username': user.USER_NAME,
                    'email': user.EMAIL,
                    'fullName': user.FULL_NAME,
                    'status': True,
                    'acceptUrl': listPath,
                    'roleId' : roleId,
                    'userId': user.USER_ID
                  }
              else:
                  return {
                    'accessToken': '',
                    'refreshToken': '',
                    'username': email,
                    'email': email,
                    'fullName': user_info.get('name'),
                    'status': False,
                    'acceptUrl': [],
                    'roleId' : ''
                  }
              
        else:
            return {"status": "error", "message": "Failed to fetch user information."}
        
def get_facebook_user_info(access_token_fb: str, db: Session):
    url = "https://graph.facebook.com/me"
    params = {
        'fields': 'id,first_name,last_name,middle_name,name,name_format,email,picture,short_name',
        'access_token': access_token_fb
    }

    response = requests.get(url, params=params)
    #response.raise_for_status()  # Kiểm tra lỗi trong phản hồi
    user_info = response.json()
    username= user_info.get('id')
    email = user_info.get('email', '')
    fullname = user_info.get('first_name')+ ' '+ user_info.get('last_name')
    if username:
      username= 'fb_'+username
      user = db_user.get_user_by_username_and_typeaccount(username, '2', db)
      if user:
          roleId = get_roleId_by_user(user, db)
          funcId = [3,4] if roleId == 1 else [4]
          path_api = get_api_path_hierarchy(funcId,roleId, db)
          listPath = hierarchical_data(path_api, Argument(keyAtrrName='FUNC_ID',
                                                          parentAtrrName='FUNC_PARENT_ID',                                                    
                                                          labelAtrrName='FUNC_NAME',
                                                          pathAtrrName='API_PATH',
                                                          iconAtrrName='ICON'
                                                          ))
          access_token = create_access_token(data={'sub': user.USER_NAME})
          refresh_token = create_refresh_token(data={'sub': user.USER_NAME})
          return {
                'accessToken': access_token,
                'refreshToken': refresh_token,
                'username': user.USER_NAME,
                'email': user.EMAIL,
                'fullName': user.FULL_NAME,
                'status': True,
                'acceptUrl': listPath,
                'roleId' : roleId
              }
      else:
            return {
                'accessToken': '',
                'refreshToken': '',
                'username': username,
                'email': email,
                'fullName': fullname,
                'status': False,
                'acceptUrl': [],
                'roleId' : ''
              }

# hàm kiểm tra email thuộc LDAP tung.nguyenson11 28/08/2023 
def check_ldap_user(username, password, db: Session):
    try:
      connection = db.connection().connection
      cursor = connection.cursor()
    except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Cannot connect to database.')
    try:
      ldap_server = os.getenv("ldap_server")
      ldap_port = int(os.getenv("ldap_port"))
      basedn = os.getenv("basedn")
      user_info = None 

      # Create an LDAP server object
      server = Server(ldap_server, get_info=ALL, port=ldap_port)

      # Create a connection
      conn = Connection(server, user= ("mobifone.vn\\" + username), password=password, authentication='NTLM')
      
      # Perform the bind
      if conn.bind():
        user = db.query(User).filter(User.USER_NAME == username).first()
        if not user:
          ldap_filter = f'(&(objectClass=USER)(objectCategory=person)(sAMAccountName={username}))'
          conn.search(basedn, ldap_filter, attributes=['sAMAccountName','displayName', 'mail','telephoneNumber'])
          user_entry = conn.entries[0]
          user_info = {
              'accessToken': '',
              'refreshToken': '',
              'username_ldap':user_entry['sAMAccountName'].value if 'sAMAccountName' in user_entry else '',
              'fullname_ldap': user_entry['displayName'].value if 'displayName' in user_entry else '',
              'email': user_entry['mail'].value if 'mail' in user_entry else '',
              'tel_num': user_entry['telephoneNumber'].value if 'telephoneNumber' in user_entry else '',
              'status': False,
              'acceptUrl': [],
              'roleId' : ''

          }
          user_info['tel_num'] = "0" + user_info['tel_num'][2:] if 'tel_num' in user_info and user_info['tel_num'].startswith("84") else user_info['tel_num']

        else:
          roleId = get_roleId_by_user(user, db)
          funcId = [3,4] if roleId == 1 else [4]
          path_api = get_api_path_hierarchy(funcId,roleId, db)
          #SINH HUNG 31/07/2023
          listPath = hierarchical_data(path_api, Argument(keyAtrrName='FUNC_ID',
                                                          parentAtrrName='FUNC_PARENT_ID',                                                    
                                                          labelAtrrName='FUNC_NAME',
                                                          pathAtrrName='API_PATH',
                                                          iconAtrrName='ICON'
                                                          ))
          
          access_token = create_access_token(data={'sub': user.USER_NAME})
          refresh_token = create_refresh_token(data={'sub': user.USER_NAME})

          user_info = {
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'username_ldap': user.USER_NAME,
            'fullName_ldap': user.FULL_NAME,
            'email': user.EMAIL,
            'tel_num': user.TEL_NUM,
            'status': True,
            'acceptUrl': listPath,
            'roleId' : roleId,
            'userId': user.USER_ID
            }
        
        cursor.close()
        connection.close()
        conn.unbind()
        return user_info
      else:
        cursor.close()
        connection.close()
        conn.unbind()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mật khẩu hoặc tài khoản không đúng. Vui lòng kiểm tra lại!")
      
    except JWTError as e:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
          detail=f'Refresh token has expired or invalid')
    

