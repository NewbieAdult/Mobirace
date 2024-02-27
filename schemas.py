from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional
from typing import Dict, Any
from fastapi import UploadFile, File
from fastapi import Form
from pydantic import  validator
#SinhHung 27/7/2023
class UserBase(BaseModel):
    username: str
    password: Optional[str] =None
    fullname: str  
    email: str
    telNumber: Optional[str] =None
    birthday: str
    gender: Optional[str]=None
    address: Optional[str]=None
    province: Optional[str]=None
    district: Optional[str]=None
    ward: Optional[str]=None
    org_id: Optional[int]=None
    child_org_id: Optional[int]=None
    size_id: Optional[int]=None
    link_fb: Optional[str]=None  
    type_account: Optional[str]=None 
    recaptcha_token: str
     

class User_Change_Password(BaseModel):
    old_password: str 
    new_password: str

class User_Reset_Password(BaseModel):
    username: str
    email: str

class UserDisplay(BaseModel):
    fullname: str 
    email: Optional[str] =None 
    telNumber: Optional[str] =None
    birthday: Optional[str]=None
    gender: Optional[str]=None
    address: Optional[str]=None
    province: Optional[str]=None
    district: Optional[str]=None
    ward: Optional[str]=None
    org_id: Optional[int]=None
    child_org_id: Optional[int]=None
    size_id: Optional[int]=None
    link_fb: Optional[str]=None  
    image : str

class RefreshTokenRequest(BaseModel):
    refresh_Token: str

class AuthLoginThird(BaseModel):
    accessToken: str
    type: str

class WebhookResponse(BaseModel):
    aspect_type: str
    event_time: int
    object_id: int
    object_type: str
    owner_id: int
    subscription_id: int
    updates: Dict[str, Any]

#####################################################

class SizeBase(BaseModel):
    SIZE_ID : int
    SIZE_NAME: str 
    class Config:
        orm_mode = True
    
class Homepage(BaseModel):
    EVENT_ID : int
    TITLE : str
    PICTURE_PATH : str
    class Config:
        orm_mode = True

class News(BaseModel):
    POST_ID : int
    TITLE : str
    IMAGE : str
    USER_CREATE : str
    CREATED_AT : Optional[str]=None
    HTML_CONTENT : str=None
    OUTSTANDING : int
    DESCRIPTION : Optional[str] = None
    UPDATE_AT : Optional[str]=None
    STATUS: int
    STATUS_NAME: Optional[str]=None
    OUTSTANDING_NAME: Optional[str]=None

    class Config:
        orm_mode = True

class Rankuser(BaseModel):
    USER_ID : int
    RANKING : int
    FULL_NAME : str
    AVATAR_PATH : str
    TOTAL_DISTANCE : float
    organization : Optional[str]
    pace : str
    class Config:
        orm_mode = True

class Rankclub(BaseModel):
    CLUB_ID : int
    CLUB_RANKING : int
    CLUB_NAME : str
    PICTURE_PATH : str
    CLUB_TOTAL_DISTANCE : float
    total_member:int
    admin_id:Optional[int]= None
    admin_name:str
    class Config:
        orm_mode = True

class SloganBase(BaseModel):
    HTML_CONTENT: str 
    class Config:
        orm_mode = True 

class ORG_BASE(BaseModel):
    ORG_ID:str
    ORG_NAME:str
    ORG_PARENT:str
    
class ORG_DISPLAY(BaseModel):
    ORG_ID : int
    ORG_NAME:str
    class Configs():
        orm_mode = True
class ORG_DISPLAY1(BaseModel):
    ORG_ID : int
    ORG_NAME:str
    ORG_PARENT_ID:int
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
    news : List[News]
    rankuser : List[Rankuser]
    rankclub : List[Rankclub]
    slogan : SloganBase
    statistic: Statistic
    class Config:
        orm_mode = True
## Xuan Bach 28/7
class ClubBase(BaseModel):
    id : int
    name : str
    description : str
    image : str
    member : int
    total_distance : float
    class Config:
        orm_mode = True

class ClubsResponse(BaseModel):
    per_page: int
    current_page: int
    total_page: int
    total_club: int
    clubs: List[ClubBase]

class UserScore(BaseModel):
    id : int
    fullname : str
    image : Optional[str]=None
    total_distance : Optional[float]=None
    ranking: Optional[int]
    pace : Optional[str]=None
    organization : Optional[str]=None
    gender : Optional[str]=None
    class Config:
        orm_mode = True

class Scoreboard(BaseModel):
    per_page: int
    total_user: int
    current_page: int
    total_page: int
    users: List[UserScore]

class DataModel(BaseModel): 
    eventid : int
    image : Optional[str]=None
    eventname : Optional[str]
    eventstartdate : Optional[str] = None
    eventenddate : Optional[str]=None
    category:Optional[str] = None
    paticipants:Optional[int]=None
    participants_running:Optional[int]= None
    event_status:Optional[str]=None
    oustanding:Optional[int]=None
    class Config:
        orm_mode = True

class EventBase(BaseModel):
    per_page: int
    total_event: int
    current_page: int
    total_page: int
    data: List[DataModel]

class Member(BaseModel):
    member_id : int
    member_name : str
    member_join_date : str
    member_rank : int
    member_image: Optional[str] = None
    member_distance : Optional[float] = None
    # member_pace: Optional[float] = None
    member_pace: Optional[str] = None
    member_gender : Optional[str] = None
    class Config:
        orm_mode = True

class NewActivate(BaseModel):
    activity_id : int
    member_id: int
    member_avatar: str
    activity_start_date : str 
    member_name : str
    activity_distance : float
    # member_pace : float
    activity_pace : str
    member_duration : Optional[str] = None
    activity_name: Optional[str] = None
    activity_type: Optional[str] = None
    activity_link_strava: Optional[int] = None 
    activity_map: Optional[str] = None,
    activity_finish: Optional[str] = None,
    status: Optional[str] = None
    reason: Optional[str] = None
    class Config:
        orm_mode = True

class ActivateMember(BaseModel):
    activity_id : int
    activity_start_date : str 
    activity_name: Optional[str] = None
    activity_distance : float
    activity_pace : str 
    activity_finish: Optional[str] = None,
    activity_type: Optional[str] = None
    calo: Optional[float] = None 
    heart_beat: Optional[float] = None
    step: Optional[float] = None
    activity_map: Optional[str] = None
    activity_link_strava: Optional[int] = None   
    activity_reason: Optional[str] = None
    activity_status: int
    class Config:
        orm_mode = True

class DetailClub(BaseModel):
    club_id : int
    club_name : str
    club_image: Optional[str] = None
    club_slogan: Optional[str] = None
    total_member : int
    total_distance : float
    founding_date : str
    club_name_admin: Optional[str] = None
    min_pace:Optional[float]=None
    max_pace:Optional[float]=None
    class Config:
        orm_mode = True

class DetailClubResponse(BaseModel):
    detail_club: DetailClub
    class Config:
        orm_mode = True

class DetailClubFor(BaseModel):
    club_id: int
    club_name: str
    club_image: Optional[str] = None
    club_slogan: Optional[str] = None
    total_member: int
    total_distance: float
    founding_date: str
    club_name_admin: Optional[str] = None
    is_admin: bool  
    user_status: str
    min_pace:Optional[float]=None
    max_pace:Optional[float]=None
    class Config:
        orm_mode = True

class DetailClubManage(BaseModel): 
    myclub: DetailClubFor
    per_page: int
    total_member: int
    current_page: int
    total_page: int
    members: List[Member]
    new_active: List[NewActivate]
    class Config:
        orm_mode = True

class PostBase(BaseModel):
    id : int
    title: Optional[str]=None
    image: Optional[str]=None
    description:Optional[str]=None
    created_at:Optional[str]=None 
    update_at:Optional[str]=None
    user_create:Optional[str]=None
    content:Optional[str]=None
    outstanding: Optional[int]=None 
    status: Optional[int]=None
    status_name: str
    outstanding_name: str
    class Config:
        orm_mode = True

class PostOutBase(BaseModel):
    id : int
    title: Optional[str]=None
    image: Optional[str]=None
    description:Optional[str]=None
    created_at:Optional[datetime]=None
    updated_at:Optional[datetime]=None
    user_create:Optional[str]=None
    outstanding: int
    status_name: str
    outstanding_name: str
    class Config:
        orm_mode = True

class PostResponse(BaseModel):
    per_page: int
    total_post: int
    current_page: int
    total_page: int
    posts: List[PostBase]

class PostOutResponse(BaseModel):
    per_page: int
    total_post: int
    current_page: int
    total_page: int
    posts: List[PostOutBase]

class PostDetail(BaseModel):
    id: int
    title:Optional[str]=None
    image:bytes
    description:Optional[str]=None
    created_at:Optional[str]=None
    content:Optional[str]=None
    user_create: str
    outstanding: str
    update_at:Optional[str]=None
    status: str
    status_name: str
    outstanding_name: str
    class Config:
        orm_mode = True

class PostDetailAccess(BaseModel):
    is_admin:bool
    id: int
    title:Optional[str]=None
    image:bytes
    description:Optional[str]=None
    created_at:Optional[str]=None
    content:Optional[str]=None
    outstanding: str
    update_at:Optional[str]=None
    status: str
    user_create: str
    status_name: str
    outstanding_name: str
    class Config:
        orm_mode = True

class AddPost(BaseModel):
    title: str = Form(...),
    description: str = Form(None),
    content: Optional[str] = Form(None),
    image: UploadFile = File(None),


class AddClub(BaseModel):
    title:str
    content:str
    image:bytes 
    min_pace:Optional[float]=None
    max_pace:Optional[float]=None
    class Config:
        orm_mode = True

class AddEvent(BaseModel):
    title:Optional[str]
    image:Optional[bytes]
    start_day:datetime
    end_day:datetime
    category:Optional[str]=None
    status:Optional[int]
    content:Optional[str]=None
    category:Optional[float]=None
    max_pace:Optional[float]=None
    min_pace:Optional[float]=None
    class Config:
        orm_mode = True

class SloganDisplay(BaseModel):
    ID: int
    HTML_CONTENT: str
    OUTSTANDING: int  
    class Config:
        orm_mode = True
class Change_admin(BaseModel):
    admin_id:int
    club_id:int
    class Config:
        orm_mode=True
class Change_admin_event(BaseModel):
    admin_id:int
    event_id:int
    class Config:
        orm_mode=True
class SearchMemberInClub(BaseModel):
    per_page: int
    total_member: int
    current_page: int
    total_page: int
    members: List[Member]

# thêm class SendEmail tung.nguyenson11 29/09/2023
class SendEmail(BaseModel):
    id: int
    class Config():
        orm_mode = True
    def __getitem__(self, item):
        return getattr(self, item)

# can.lt 14/10/23
class FraudulentActivity(BaseModel):
    event_id: int = None
    club_id: int = None
    user_id: int
    run_id: int
    reason: str = None
