## Xuân Bách - 28/7/2023
# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_scoreboard
from typing import Optional
from schemas import Scoreboard
from utils.base_url import get_base_url
router = APIRouter(
    prefix='/scoreboard',
    tags=['scoreboard']
)

@router.get('/', response_model=Scoreboard)
def get_user_scoreboard(current_page: int = Query(1, alias='current_page'),
                        per_page: int = Query(10, alias='per_page'),
                        month: Optional[int] = Query(None),
                        year: Optional[int] = Query(None), 
                        db: Session = Depends(get_db), 
                        host: str = Depends(get_base_url)):
    return db_scoreboard.get_user_scoreboard_data(host, current_page=current_page, 
                                                  per_page=per_page, 
                                                  month=month, 
                                                  year=year,
                                                  db=db)
#Sinh Hung 3/8/2023
@router.get('/search', response_model=Scoreboard)
def search_user(text_search:str, per_page : int = Query(10), current_page : int=Query(1),
                        db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_scoreboard.get_user_by_fullname(host, text_search, per_page,current_page,db)