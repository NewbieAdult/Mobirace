from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_slogan
from schemas import SloganDisplay, SloganBase
from typing import List

router = APIRouter(
    prefix='/slogan',
    tags=['slogan']
)

@router.get('/all', response_model= List[SloganDisplay])
def get_all_slogans_route(db: Session = Depends(get_db)):
    slogans = db_slogan.get_all_slogans(db)
    if slogans:
        return slogans
    else:
        raise HTTPException(status_code=404, detail="No slogans found")

@router.post('/create')
def create_slogan_router(slogan: SloganBase, db: Session = Depends(get_db)):
    return db_slogan.create_slogan(db, slogan.HTML_CONTENT)

@router.put('/update')
def update_slogan_router(slogan_id: int, slogan_update: SloganBase, db: Session = Depends(get_db)):
    return db_slogan.update_slogan(db, slogan_id, slogan_update)

@router.delete('/delete')
def delete_slogan_router(slogan_id: int, db: Session = Depends(get_db)):
    return db_slogan.delete_slogan(db, slogan_id)

@router.put('/set-outstanding')
def set_outstanding_slogan_router(slogan_id: int, db: Session = Depends(get_db)):
    return db_slogan.set_outstanding_slogan(db, slogan_id)

@router.get('/search')
def search_slogan_router(name: str, db: Session = Depends(get_db)):
    return db_slogan.search_slogan(db, name)