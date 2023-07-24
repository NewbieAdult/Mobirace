from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Club
from sqlalchemy import desc

#get community
def get_community(db: Session, num_events : int = 4):
  return db.query(Club).order_by(desc(Club.CREATE_AT)).limit(num_events).all()

