from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_org
from typing import List
from schemas import ORG_DISPLAY,ORG_BASE

router=APIRouter(
    prefix='/org',
    tags=['org']
)

#get_all_arg
@router.get('/',response_model=List[ORG_DISPLAY])
def get_all_org(db: Session = Depends(get_db)):
    return db_org.get_all_orgs(db)
@router.get('/{parent}',response_model=List[ORG_DISPLAY])
def get_org_by_parent_id(parent:str,db: Session = Depends(get_db)):
    return db_org.get_org_by_parent(db,parent)