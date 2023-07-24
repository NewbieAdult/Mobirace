from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from typing import List
from db import db_listsize
from schemas import SizeBase

router = APIRouter(
    prefix='/listsize',
    tags=['size']
)

# Read all size
@router.get('/', response_model=List[SizeBase])
def get_all_size(db: Session = Depends(get_db)):
  return db_listsize.get_all_size(db)