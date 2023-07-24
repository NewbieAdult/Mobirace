from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_homepage, db_community, db_rankclub, db_rankuser, db_slogan, db_statistic  
from schemas import Home

router = APIRouter(
    prefix='/home',
    tags=['home']
)

@router.get('/', response_model=Home)
def get_home(db: Session = Depends(get_db)):
    homepage_data = db_homepage.get_homepage(db)
    community_data = db_community.get_community(db)
    rankuser_data = db_rankuser.get_rankuser(db)
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
        "total_race": total_race}

    return Home(
        homepage=homepage_data,
        community=community_data,
        rankclub=rankclub_data,
        rankuser=rankuser_data,
        slogan=slogan_data,
        member=member_count,
        total_distance=total_distance,
        total_club=total_club,
        statistic=statistic_data
    )


    



