from sqlalchemy.orm.session import Session
from db.models import Club, User, User_Club
from schemas import Rankclub
from sqlalchemy import func
from fastapi import HTTPException
import os
from dotenv import load_dotenv
load_dotenv()
host = os.getenv("host")

#get rankclub
def get_rankclub(db: Session):
    try:
        clubs = db.query(Club).order_by(Club.CLUB_TOTAL_DISTANCE.desc()).limit(8).all()
        rankclub_data = []
        for club in clubs:
            admin_user = db.query(User).filter(User.USER_ID == club.ADMIN).first()
            admin_name = admin_user.FULL_NAME if admin_user is not None else ""
            total_member = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club.CLUB_ID).scalar()
            image_path = club.PICTURE_PATH.replace("\\", "/")
            rankclub = Rankclub(
                CLUB_ID=club.CLUB_ID,
                CLUB_RANKING=club.CLUB_RANKING,
                CLUB_NAME=club.CLUB_NAME,
                PICTURE_PATH=f"{host}/{image_path}",
                CLUB_TOTAL_DISTANCE=round(club.CLUB_TOTAL_DISTANCE, 2) if club.CLUB_TOTAL_DISTANCE is not None else 0,
                total_member=total_member,
                admin_id=club.ADMIN,
                admin_name=admin_name
            )
            rankclub_data.append(rankclub)
        return rankclub_data
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị bảng xếp hạng câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")