from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import User

#get rankuser
def get_rankuser(db: Session):
  return db.query(User).order_by(User.RANKING.asc()).all()
