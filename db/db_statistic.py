from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm.session import Session
from db.models import User, Club, Event

#count_member
def count_users(db: Session):
    return db.query(func.count(User.USER_ID)).scalar()

#total_distance
def total_distance(db: Session):
    total_distance = db.query(func.sum(User.TOTAL_DISTANCE)).scalar()
    rounded_distance = round(total_distance or 0, 1)
    return rounded_distance

#total_club
def total_club(db: Session):
    return db.query(func.count(Club.CLUB_ID)).scalar()

#total_race
def total_race(db: Session):
    return db.query(func.count(Event.EVENT_ID)).scalar()