## Xuân Bách - 27/7/2023
# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_event, db_news, db_rankclub, db_rankuser, db_slogan, db_statistic, db_slogan  
from schemas import Home
from utils.base_url import get_base_url
router = APIRouter(
    prefix='/home',
    tags=['home']
)

@router.get('/', response_model=Home)
def get_home(db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    homepage_data = db_event.get_homepage(host, db)
    news_data = db_news.get_news(host, db)
    rankuser_data = db_rankuser.get_rankuser(host, db)
    rankclub_data = db_rankclub.get_rankclub(db)
    slogan_data = db_slogan.get_slogan(db)
    member_count = db_statistic.count_users(db)
    total_distance = db_statistic.total_distance(db)
    total_club = db_statistic.total_club(db)
    total_race = db_statistic.total_race(db)
    statistic_data = {
        "member": member_count,
        "total_distance": total_distance,
        "total_club": total_club,
        "total_race": total_race
    }

    return Home(
        homepage=homepage_data,
        news=news_data,
        rankuser=rankuser_data,
        rankclub=rankclub_data,
        slogan=slogan_data,
        statistic=statistic_data
    )




