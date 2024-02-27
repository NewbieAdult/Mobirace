# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import Query, Depends, HTTPException
from sqlalchemy import func, desc, extract
from sqlalchemy.orm.session import Session
from db.models import User, Organization, Organization_Child, Run
from db.database import get_db
from schemas import UserScore, Scoreboard  
from math import ceil
from typing import Optional
from datetime import datetime
from utils.format import format_seconds

def get_user_scoreboard_data(host: str, current_page: int = Query(1, alias='current_page'), per_page: int = Query(10, alias='per_page'), month: Optional[int] = Query(None), year: Optional[int] = Query(datetime.now().year), db: Session = Depends(get_db)):
    try:
        if month is not None:
            users_month = db.query(User, 
                              Organization, 
                              Organization_Child,
                              func.sum(Run.DISTANCE).label('total_distance'),
                              func.avg(Run.PACE).label('pace')) \
                .outerjoin(Organization, User
                           .ORG_ID == Organization.ORG_ID) \
                .outerjoin(Organization_Child, User.ORG_CHILD_ID == Organization_Child.CHILD_ID) \
                .outerjoin(Run, Run.USER_ID == User.USER_ID) \
                .filter(func.extract('year', Run.CREATED_AT) == year, func.extract('month', Run.CREATED_AT) == month) \
                .order_by(desc('total_distance'), 'pace') \
                .group_by(User, Organization, Organization_Child) \
                .all()
            total_user = len(users_month)
            all_user_info = []
            for idx, (user, organization, org_child, total_distance, pace) in enumerate(users_month, start=1): 
                image_path = user.AVATAR_PATH.replace("\\", "/")
                avatar_path = f"{host}/{image_path}"
                avatar_path = avatar_path if user.AVATAR_PATH is not None else ""
                organization_child = " - " + org_child.CHILD_NAME if org_child else ""
                organization = organization.ORG_NAME if organization else ""
                user_data = UserScore(
                    id=user.USER_ID,
                    fullname=user.FULL_NAME if user.FULL_NAME is not None else "",
                    image=avatar_path,
                    total_distance=round(total_distance, 2) if total_distance is not None else 0,
                    ranking=idx,
                    pace=format_seconds(int((pace if pace is not None else 0) * 60)),
                    organization= organization + (organization_child if organization_child !=" - " else ""),
                    gender=user.GENDER,
                )
                all_user_info.append(user_data)
        else:   
            query = db.query(User, Organization, Organization_Child) \
                    .outerjoin(Organization, User.ORG_ID == Organization.ORG_ID) \
                    .outerjoin(Organization_Child, User.ORG_CHILD_ID == Organization_Child.CHILD_ID)
                    
            users = query.order_by(desc(User.TOTAL_DISTANCE), User.PACE).all()
            total_user = len(users)
            all_user_info = []
            for idx, (user, organization, org_child) in enumerate(users, start=1): 
                image_path = user.AVATAR_PATH.replace("\\", "/")
                avatar_path = f"{host}/{image_path}"
                avatar_path = avatar_path if user.AVATAR_PATH is not None else ""
                organization_child = " - " + org_child.CHILD_NAME if org_child else ""
                organization = organization.ORG_NAME if organization else ""
                user_data = UserScore(
                    id=user.USER_ID,
                    fullname=user.FULL_NAME if user.FULL_NAME is not None else "",
                    image=avatar_path,
                    total_distance=round(user.TOTAL_DISTANCE, 2) if user.TOTAL_DISTANCE is not None else 0,
                    ranking=idx,
                    pace=format_seconds(int((user.PACE if user.PACE is not None else 0) * 60)),
                    organization= organization + (organization_child if organization_child !=" - " else ""),
                    gender=user.GENDER,
                )
                all_user_info.append(user_data)

        total_page = ceil(total_user / per_page)
        start_index = (current_page - 1) * per_page
        end_index = start_index + per_page
        users_on_page = all_user_info[start_index:end_index]
        return Scoreboard(
            per_page=per_page,
            total_user=total_user,
            current_page=current_page,
            total_page=total_page,
            users=users_on_page,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị bảng xếp hạng cá nhân! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#Sinh Hung 3/8/2023
def get_user_by_fullname(host, text_search:str, per_page : int, current_page : int, db: Session):
    try:
        skip = (current_page - 1) * per_page
        users = db.query(User, Organization, Organization_Child).\
        outerjoin(Organization, User.ORG_ID == Organization.ORG_ID). \
        outerjoin(Organization_Child, User.ORG_CHILD_ID == Organization_Child.CHILD_ID). \
        filter(User.FULL_NAME.ilike(f"%{text_search}%"))
        total_user = users.count()
        users = users.offset(skip).limit(per_page).all()
        result = []
        for user, organization, org_child in users:
            fullname = user.FULL_NAME if user.FULL_NAME is not None else ""
            image_path = user.AVATAR_PATH.replace("\\", "/")
            avatar_path = f"{host}/{image_path}"
            avatar_path = avatar_path if user.AVATAR_PATH is not None else ""
            organization_name = organization.ORG_NAME if organization else ""
            organization_child = " - " + org_child.CHILD_NAME if org_child else ""
            user_data = UserScore(
                id=user.USER_ID,
                fullname=fullname,
                image=avatar_path,
                total_distance=round(user.TOTAL_DISTANCE, 2) if user.TOTAL_DISTANCE is not None else 0,
                ranking=user.RANKING,
                pace=format_seconds(int((user.PACE if user.PACE is not None else 0) * 60)),
                organization= organization_name + (organization_child if organization_child != " - " else ""),
                gender=user.GENDER
            )
            result.append(user_data)
        total_page = ceil(int(total_user) / per_page)
        return Scoreboard(
            per_page=per_page,
            total_user=total_user,
            current_page=current_page,
            total_page=total_page,
            users=result
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi tìm kiếm người dùng trên bảng xếp hạng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

