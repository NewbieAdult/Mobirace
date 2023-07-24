from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Club

#get rankclub
def get_rankclub(db: Session):
  return db.query(Club).order_by(Club.CLUB_RANKING.asc()).all()