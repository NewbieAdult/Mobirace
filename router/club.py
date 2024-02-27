## Xuân Bách - 28/7/2023
# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, Query, Form, UploadFile
from sqlalchemy.orm.session import Session
from db.database import get_db
from db import db_club
from typing import Optional, Union
from schemas import ClubsResponse,Change_admin,FraudulentActivity
from db.models import User
from auth.oauth2 import get_current_user
from utils.base_url import get_base_url
from jobs.tasks import *
from datetime import datetime

router = APIRouter(
    prefix='/club',
    tags=['club']
)
# thien.tranthi add host: str = Depends(get_base_url)
@router.get('/', response_model=ClubsResponse)
def get_all_clubs_info( search_text: Optional[str] = None,
                        current_page: int = Query(1, alias='current_page'), 
                        per_page: int = Query(5, alias='per_page'), 
                        db: Session = Depends(get_db), 
                        host: str = Depends(get_base_url)):
    return db_club.get_all_clubs_info(host, search_text, current_page=current_page, per_page=per_page, db=db)

# thien.tranthi add host: str = Depends(get_base_url)
@router.get('/detail-club/{club_id}')
def get_club_details_route(club_id: int, 
                           db: Session = Depends(get_db), 
                           host: str = Depends(get_base_url)):
    return db_club.get_club_details(host, 
                                    club_id, 
                                    db)
# thien.tranthi add host: str = Depends(get_base_url)
@router.get('/search', response_model=ClubsResponse)
def search_club(search:str, per_page: int = Query(5),current_page: int = Query(1), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_club_by_clubname(host, search, per_page, current_page, db)

@router.post('/add-club')
def create_club_route(  title: str = Form(...),
                        content: Optional[str] = Form(None),
                        image: Union[UploadFile,str] = Form(None),
                        min_pace: Optional[float]=Form(None),
                        max_pace: Optional[float]=Form(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db_club.create_club(db=db, current_user=current_user,
                               title=title
                               ,content=content
                               ,min_pace=min_pace
                               ,max_pace=max_pace
                               ,image=image
                               )

@router.put('/update/{club_id}', status_code=200)
def update_club_route(  club_id: int, 
                        title: str = Form(...),
                        content: Optional[str] = Form(None),
                        image: Union[UploadFile,str] = Form(None),
                        min_pace: Optional[float]=Form(None),
                        max_pace: Optional[float]=Form(None), db: Session = Depends(get_db)):
    return db_club.update_club(db=db, 
                               club_id=club_id 
                               ,title=title
                               ,content=content
                               ,min_pace=min_pace
                               ,max_pace=max_pace
                               ,image=image)

@router.delete('/delete/{club_id}', status_code=200)
def delete_club_route(club_id: int, db: Session = Depends(get_db)):
    return db_club.delete_club(club_id=club_id, db=db)

@router.post("/join-club/{club_id}")
def join_club_route(club_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db_club.join_club(club_id=club_id, current_user=current_user, db=db)

@router.delete("/leave-club/{club_id}")
def leave_club_route(club_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db_club.leave_club(club_id=club_id, current_user=current_user, db=db)

@router.delete("/delete-memberclub/{club_id}/{user_id}", status_code=200)
def remove_user_from_club_route(club_id: int, user_id: int, current_user:User=Depends(get_current_user), db: Session = Depends(get_db)):
    return db_club.remove_user_from_club(user_id=user_id, club_id=club_id, current_user=current_user, db=db)

@router.get('/myclub')
def get_my_club(current_user: User = Depends(get_current_user), current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_user_clubs(host, current_user=current_user, current_page=current_page, per_page=per_page, db=db)

# thien.tranthi add host: str = Depends(get_base_url)
@router.get('/club-detail/{club_id}')
def get_detail_club_route(club_id: int, 
                          current_user : User = Depends(get_current_user), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_detail_club_1(host=host, club_id=club_id, current_user=current_user, db=db)

@router.put('/change-adminclub')
def change_admin_club(request:Change_admin,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return db_club.change_admin_club(request=request,current_user=current_user,db=db)

@router.get("/club/active-user-club")
def get_active_user_club(club_id: int, user_id: int,db:Session=Depends(get_db)):
    return db_club.get_active_user_club(club_id=club_id,user_id=user_id,db=db)

@router.get("/club/club-manage/search")
def search_club_members(club_id: int, search: str, month: Optional[int] = None,
                     current_page: int = Query(1, alias='current_page'),
                     per_page: int = Query(10, alias='per_page'),
                     db: Session = Depends(get_db)):
    return db_club.search_club_members(club_id, search, month, current_page, per_page, db)

@router.get("/active-user-club")
def get_active_user_club(club_id: int, user_id: int,db:Session=Depends(get_db)):
    return db_club.get_user_club_activity(club_id=club_id,user_id=user_id,db=db)
@router.get("/active-user-club-by-date")
def get_active_user_club_by_date(club_id: int,user_id: int,textSearch:str,db:Session=Depends(get_db)):
    return db_club.get_user_club_activity_by_date(club_id=club_id,user_id=user_id,db=db,textSearch=textSearch)

# @router.put("/delete-activeclub")
# def delete_activeevent(run_id: int,club_id: int,reason:str,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
#     return db_club.hide_activity_in_club(run_id=run_id,club_id=club_id,reason=reason,db=db,current_user=current_user)

#can.lt 14/10/23
@router.put("/deactive-activity")
def deactive_activity(run_id: int,club_id: int,reason:str,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_club.deactive_activity(FraudulentActivity(run_id=run_id,
                                                        club_id=club_id,
                                                        reason=reason,
                                                        user_id=current_user.USER_ID),db=db)

#can.lt 14/10/23
@router.put("/active-activity")
def deactive_activity(run_id: int,club_id: int,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_club.active_activity(FraudulentActivity(run_id=run_id,
                                                      club_id=club_id,
                                                      user_id=current_user.USER_ID),db=db)

@router.put("/re-delete-activeclub")
def re_delete_activeevent(run_id: int ,club_id: int,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_club.re_hide_activity_in_club(run_id=run_id,club_id=club_id,db=db,current_user=current_user)

#API hiển thị danh sách thành viên trong club tung.nguyenson11 28/09/2023
@router.get('/rank-member/{club_id}')
def get_members_club(club_id: int, 
                           month: Optional[int] = None,
                           year: Optional[int] = None, 
                           search_name: Optional[str] = None, 
                           current_page: int = Query(1, alias='current_page'), 
                           per_page: int = Query(10, alias='per_page'), 
                           db: Session = Depends(get_db), 
                           host: str = Depends(get_base_url)):
    return db_club.get_members_club(host, 
                                    club_id, 
                                    month, 
                                    year,
                                    search_name, 
                                    current_page,
                                    per_page,
                                    db)
#API hiển thị danh sách thành viên trong club tung.nguyenson11 28/09/2023
@router.get('/club-detail/rank-member/{club_id}')
def get_members_club(club_id: int, 
                           month: Optional[int] = None,
                           year: Optional[int] = None, 
                           search_name: Optional[str] = None, 
                           current_page: int = Query(1, alias='current_page'), 
                           per_page: int = Query(10, alias='per_page'), 
                           db: Session = Depends(get_db), 
                           host: str = Depends(get_base_url)):
    return db_club.get_members_club_1(host, 
                                    club_id, 
                                    month, 
                                    year,
                                    search_name, 
                                    current_page,
                                    per_page,
                                    db)

# API hiển thị danh sách hoạt động của câu lạc bộ tung.nguyenson11 28/09/2023
@router.get('/new-activity/{club_id}')
def get_members_club(club_id: int, 
                        hour: Optional[int] = 48, 
                        search_name: Optional[str] = None, 
                        current_page: int = Query(1, alias='current_page'), 
                        per_page: int = Query(10, alias='per_page'), 
                        db: Session = Depends(get_db), 
                        host: str = Depends(get_base_url)):
    return db_club.get_new_activities_club_main( host, 
                                            club_id, 
                                            hour, 
                                            search_name, 
                                            current_page,
                                            per_page,
                                            db)

# API hiển thị danh sách hoạt động của câu lạc bộ tung.nguyenson11 28/09/2023
@router.get('/club-detail/new-activities/{club_id}')
def get_members_club(club_id: int, 
                        hour: Optional[int] = 48, 
                        search_name: Optional[str] = None, 
                        current_page: int = Query(1, alias='current_page'), 
                        per_page: int = Query(10, alias='per_page'), 
                        db: Session = Depends(get_db), 
                        host: str = Depends(get_base_url)):
    return db_club.get_new_activities_club( host, 
                                            club_id, 
                                            hour, 
                                            search_name, 
                                            current_page,
                                            per_page,
                                            db)

# API hiển thị thông tin chi tiết câu lạc bộ sau khi đăng nhập tung.nguyenson11 15/10/2023
@router.get('/overview/{club_id}')
def get_detail_club_route(club_id: int, 
                          current_user : User = Depends(get_current_user), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_detail_club(host=host, club_id=club_id, current_user=current_user, db=db)

# API hiển thị thông tin chi tiết thành viên trong câu lạc bộ tung.nguyenson11 15/10/2023
@router.get('/member/overview')
def get_detail_club_route(club_id: int,
                          member_id: int, 
                          db: Session = Depends(get_db), host: str = Depends(get_base_url),
                        #   current_user:User=Depends(get_current_user_public)
                          ):
    return db_club.get_detail_member_club(host=host, club_id=club_id, member_id=member_id, db=db, user_id=None)

# API hiển thị thông tin chi tiết thành viên trong câu lạc bộ sau khi login tung.nguyenson11 15/10/2023
@router.get('/member/overview_login')
def get_detail_club_route(club_id: int,
                          member_id: int, 
                          db: Session = Depends(get_db), host: str = Depends(get_base_url),
                          current_user:User=Depends(get_current_user)
                          ):
    return db_club.get_detail_member_club(host=host, club_id=club_id, member_id=member_id, db=db, user_id=current_user.USER_ID)

# API hiển thị thông tin chi tiết câu lạc bộ trước khi đăng nhập tung.nguyenson11 15/10/2023
@router.get('/overview_public/{club_id}')
def get_detail_club_route(club_id: int, 
                             db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_detail_club_no_acc(host=host, club_id=club_id, db=db)

# API hiển thị thông tin chi tiết hoạt động thành viên trong câu lạc bộ tung.nguyenson11 15/10/2023
@router.get('/member/activities')
def get_detail_club_route(club_id: int,
                          member_id: int,
                          current_page: int = Query(1, alias='current_page'), 
                          per_page: int = Query(10, alias='per_page'),
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          activity_name: Optional[str] = None,
                          db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_club.get_detail_member_activities_club(host=host, 
                                                    club_id=club_id, 
                                                    member_id=member_id,
                                                    current_page=current_page,
                                                    per_page=per_page,
                                                    from_date=from_date,
                                                    to_date=to_date,
                                                    activity_name=activity_name,
                                                    db=db, 
                                                    user_id=None)

# API hiển thị thông tin chi tiết hoạt động thành viên trong câu lạc bộ sau khi login tung.nguyenson11 15/10/2023
@router.get('/member/activities_login')
def get_detail_club_route(club_id: int,
                          member_id: int,
                          current_page: int = Query(1, alias='current_page'), 
                          per_page: int = Query(10, alias='per_page'),
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          activity_name: Optional[str] = None,
                          db: Session = Depends(get_db), host: str = Depends(get_base_url),
                          current_user:User=Depends(get_current_user)):
    return db_club.get_detail_member_activities_club(host=host, 
                                                    club_id=club_id, 
                                                    member_id=member_id,
                                                    current_page=current_page,
                                                    per_page=per_page,
                                                    from_date=from_date,
                                                    to_date=to_date,
                                                    activity_name=activity_name,
                                                    db=db,
                                                    user_id=current_user.USER_ID)


