# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from sqlalchemy.orm.session import Session
from db.models import User, Organization
from schemas import Rankuser
from fastapi import HTTPException
from sqlalchemy import desc  
from utils.format import format_seconds
import os

#get rankuser
def get_rankuser(host: str, db: Session):
    try:
        users = db.query(User).order_by(desc(User.TOTAL_DISTANCE), User.PACE).limit(10).all()
        rankuser_data = []
        for i, user in enumerate(users):  
            organization = db.query(Organization).filter(Organization.ORG_ID == user.ORG_ID).first()
            # total_seconds = int(user.PACE * 60)  # Chuyển đổi thành số giây
            # hours = total_seconds // 3600
            # minutes = (total_seconds % 3600) // 60
            # seconds = total_seconds % 60
            image_path = user.AVATAR_PATH.replace("\\", "/")
            avatar_path = f"{host}/{image_path}"
            rankuser = Rankuser(
                USER_ID=user.USER_ID,
                RANKING=i+1,
                FULL_NAME=user.FULL_NAME if user.FULL_NAME is not None else "",
                AVATAR_PATH= avatar_path if user.AVATAR_PATH is not None else "",
                TOTAL_DISTANCE=round(user.TOTAL_DISTANCE or 0,2) if user.TOTAL_DISTANCE is not None else 0 ,
                organization=organization.ORG_NAME if organization is not None else "",
                # pace=rf"{hours:02d}:{minutes:02d}:{seconds:02d}"
                pace=format_seconds(int((user.PACE if user.PACE is not None else 0) * 60))
            )
            rankuser_data.append(rankuser)
        return rankuser_data
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị bảng xếp hạng người dùng trên trang chủ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
