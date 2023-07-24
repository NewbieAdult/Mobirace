from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    username: str
    password: str
    fullname: str  
    email: str
    telNumber: Optional[str] =None
    birthday: str
    gender: str
    address: Optional[str]=None
    province: Optional[str]=None
    district: Optional[str]=None
    ward: Optional[str]=None
    org_id: Optional[str]=None
    child_org_id: Optional[str]=None
    size_id: str
    link_fb: Optional[str]=None  

class User_Change_Password(BaseModel):
    old_password: str
    new_password: str

# Tạo một Pydantic model để định nghĩa cấu trúc của request body
class RefreshTokenRequest(BaseModel):
    refresh_Token: str

class SizeBase(BaseModel):
    SIZE_NAME: str 
    class Config:
        orm_mode = True
    
class Homepage(BaseModel):
    TITLE : str
    PICTURE_PATH : str
    class Config:
        orm_mode = True

class Community(BaseModel):
    CLUB_NAME : str
    PICTUTE_PATH : str
    class Config:
        orm_mode = True

class Rankuser(BaseModel):
    RANKING : int
    FULL_NAME : str
    AVATAR_PATH : str
    TOTAL_DISTANCE : str
    class Config:
        orm_mode = True

class Rankclub(BaseModel):
    CLUB_RANKING : int
    CLUB_NAME : str
    PICTUTE_PATH : str
    CLUB_TOTAL_DISTANCE : str
    class Config:
        orm_mode = True

class Slogan(BaseModel):
    HTML_CONTENT: str 
    class Config:
        orm_mode = True 

class ORG_BASE(BaseModel):
    ORG_ID:str
    ORG_NAME:str
    ORG_PARENT:str
    
class ORG_DISPLAY(BaseModel):
    ORG_NAME:str
    class Configs():
        orm_mode = True

class Statistic(BaseModel):
    member : int
    total_distance : float
    total_club : int
    total_race : int
    class Config:
        orm_mode = True 

class Home(BaseModel):
    homepage : List[Homepage]
    community : List[Community]
    rankuser : List[Rankuser]
    rankclub : List[Rankclub]
    slogan : List[Slogan]
    statistic: Statistic
    class Config:
        orm_mode = True