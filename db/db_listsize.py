from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Shirt_Size

#get all size
def get_all_size(db: Session):
  return db.query(Shirt_Size).all()