## Xuân Bách - 29/7/2023
# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, Query, Form, UploadFile
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_event
from typing import Union
from schemas import EventBase, FraudulentActivity, Change_admin_event
from db.models import User
from auth.oauth2 import get_current_user
from datetime import datetime
from utils.base_url import get_base_url
router = APIRouter(
    prefix='/event',
    tags=['event']
)

@router.get("/", response_model=EventBase)
def get_events_route(status:int,current_page: int = Query(1, alias='current_page'), per_page: int = Query(10, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_event.get_events_info(host, db,status=status, current_page=current_page, per_page=per_page)

@router.get("/search", response_model=EventBase)
def get_event_by_eventname(status:int, eventname :str, per_page: int = Query(10, alias='per_page'), current_page: int = Query(1, alias='current_page'),db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_event.get_event_by_eventname(host, eventname, status, per_page=per_page, current_page=current_page, db=db)

@router.post('/add-event')
def create_post_route(  title: str = Form(...),
                        image: Union[UploadFile,str] = Form(None),
                        start_day: datetime = Form(...),
                        end_day: datetime = Form(...),
                        category: str = Form(None),
                        content: str = Form(None),
                        max_pace: float = Form(None),
                        min_pace: float = Form(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db_event.create_event(db=db, current_user=current_user,  title=title,
                                                                    image=image,
                                                                    start_day=start_day,
                                                                    end_day=end_day,
                                                                    category=category,
                                                                    content=content,
                                                                    max_pace=max_pace,
                                                                    min_pace=min_pace)

@router.post("/join-event/{event_id}")
def join_event_route(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db_event.join_event(event_id=event_id, current_user=current_user, db=db)

@router.delete("/leave-event/{event_id}")
def leave_event_route(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db_event.leave_event(event_id=event_id, current_user=current_user, db=db)

@router.put('/update/{event_id}', status_code=200)
def update_event_route( event_id:int, 
                        title: str = Form(...),
                        image: Union[UploadFile,str] = Form(None),
                        start_day: datetime = Form(...),
                        end_day: datetime = Form(...),
                        category: str = Form(None),
                        status: int = Form(None),
                        content: str = Form(None),
                        max_pace: float = Form(None),
                        min_pace: float = Form(None), 
                        db: Session = Depends(get_db)):
    return db_event.update_event(event_id=event_id, 
                                title=title,
                                image=image,
                                start_day=start_day,
                                end_day=end_day,
                                category=category,
                                status=status,
                                content=content,
                                max_pace=max_pace,
                                min_pace=min_pace, db=db)
# delete event thien.tranthi 19/10/2023
@router.delete('/delete/{event_id}', status_code=200)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    return db_event.delete_event(event_id=event_id, db=db)
# change admin event thien.tranthi 19/10/2023
@router.put('/change-adminevent')
def change_admin_event(request:Change_admin_event,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return db_event.change_admin_event(request=request,current_user=current_user,db=db)

@router.get("/active-user-event")
def get_active_user_event(event_id: int, user_id: int,db:Session=Depends(get_db)):
    return db_event.get_user_event_activity(event_id=event_id,user_id=user_id,db=db)

@router.get("/active-user-event-by-date")
def get_active_user_event_by_date(event_id: int, user_id: int,textSearch:str,db:Session=Depends(get_db)):
    return db_event.get_user_event_activity_by_date(event_id=event_id,user_id=user_id,db=db,textSearch=textSearch)

@router.put("/delete-activeevent")
def delete_activeevent(run_id: int ,event_id: int,reason:str,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_event.hide_activity_in_event(run_id=run_id,event_id=event_id,reason=reason,db=db,current_user=current_user)

@router.put("/re-delete-activeevent")
def re_delete_activeevent(run_id: int ,event_id: int,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_event.re_hide_activity_in_event(run_id=run_id,event_id=event_id,db=db,current_user=current_user)

@router.put("/set-outstanding")
def set_outstanding(event_id:int,db:Session=Depends(get_db)):
    return db_event.set_outstanding(event_id, db)

@router.put("/un-set-outstanding")
def un_set_outstanding(event_id:int,db:Session=Depends(get_db)):
    return db_event.un_set_outstanding(event_id, db)

#can.lt 15/10/23
@router.put("/deactive-activity")
def deactive_activity(run_id: int,event_id: int,reason:str,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_event.deactive_activity(FraudulentActivity(run_id=run_id,
                                                        event_id=event_id,
                                                        reason=reason,
                                                        user_id=current_user.USER_ID),db=db)

#can.lt 15/10/23
@router.put("/active-activity")
def deactive_activity(run_id: int,event_id: int,db: Session = Depends(get_db),current_user:User=Depends(get_current_user)):
    return db_event.active_activity(FraudulentActivity(run_id=run_id,
                                                        event_id=event_id,
                                                        user_id=current_user.USER_ID),db=db)