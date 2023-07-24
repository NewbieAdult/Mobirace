from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Event
from sqlalchemy import desc

#get homepage
def get_homepage(db: Session, num_events : int = 3):
  return db.query(Event).order_by(desc(Event.CREATE_AT)).limit(num_events).all()
