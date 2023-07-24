from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm.session import Session
from db.database import get_db
from db.db_area import get_provinces_list, get_districts_list, get_wards_list

router = APIRouter(
    tags=['area'],
    prefix = '/area'
)

@router.get('/province')
def get_province(db: Session = Depends(get_db)):
    return get_provinces_list(db)

@router.get('/district')
def get_district(province: str = Form(None),db: Session = Depends(get_db)):
    return get_districts_list(db, province)

@router.get('/ward')
def get_ward(province: str = Form(None), district: str = Form(None),db: Session = Depends(get_db)):
    return get_wards_list(db, province, district)