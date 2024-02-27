from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_chart
router = APIRouter(
    prefix='/chart',
    tags=['chart']
)
@router.get("/date/{user_id}")
def get_by_day(user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_by_day(db=db,user_id=user_id)
@router.get("/month/{user_id}")
def get_by_month(user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_by_month(db=db,user_id=user_id)
# API lấy thông tin hoạt động của club-id trong 14 ngày gần nhất cho đến hiện tại thien.tranthi 19/10/2023
@router.get("/date/club/")
def get_club_by_day(club_id: int, user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_club_by_day(db=db,user_id=user_id, club_id=club_id)

# API lấy thông tin hoạt động của club-id theo tháng thien.tranthi 19/10/2023  
@router.get("/month/club/")
def get_club_by_month(club_id: int, user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_club_by_month(db=db,user_id=user_id, club_id=club_id)

# API lấy thông tin hoạt động của club-id trong 14 ngày gần nhất cho đến hiện tại thien.tranthi 19/10/2023
@router.get("/date/event/")
def get_events_by_day(event_id: int, user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_event_by_day(db=db,user_id=user_id, event_id=event_id)

# API lấy thông tin hoạt động của club-id theo tháng thien.tranthi 19/10/2023  
@router.get("/month/event/")
def get_events_by_month(event_id: int, user_id:int,db: Session = Depends(get_db)):
    return db_chart.get_event_by_month(db=db,user_id=user_id, event_id=event_id)

