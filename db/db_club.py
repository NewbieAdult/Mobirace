# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import Query, Depends, HTTPException, Form, UploadFile
from sqlalchemy import func, delete, desc, or_
from sqlalchemy.orm.session import Session
from db.models import Club, User_Club, User, Run, User_Club_Activity, Flaudulent_Activity_Club
from db.database import get_db
from schemas import ClubBase, ClubsResponse, DetailClub, Member, NewActivate, DetailClubFor,Change_admin, SearchMemberInClub, FraudulentActivity, ActivateMember
from math import ceil
from typing import Dict, List, Optional, Union
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from jobs.tasks import *
from auth.oauth2 import get_current_user
from utils.format import format_seconds
import os, shutil, threading
import pytz

#get clubs
def get_all_clubs_info(host: str, search_text: Optional[str] = None,current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db)):
    try:
        skip = (current_page - 1) * per_page
        if search_text != 'undefined' and search_text != '':
            clubs = db.query(Club).\
                    outerjoin(User_Club, Club.CLUB_ID == User_Club.c.CLUB_ID).\
                    filter(Club.CLUB_NAME.ilike(f"%{search_text}%"))
            total_club = clubs.count()
            clubs = clubs.offset(skip).limit(per_page).all()
        else:    
            clubs = db.query(Club).order_by(desc(Club.CLUB_TOTAL_DISTANCE)).offset(skip).limit(per_page).all()
            total_club = db.query(func.count(Club.CLUB_ID)).scalar()
        all_club_info = []
        for club in clubs:
            member = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club.CLUB_ID).scalar()
            image_path = club.PICTURE_PATH.replace("\\", "/")
            club_data = ClubBase(
                id=club.CLUB_ID,
                name=club.CLUB_NAME,
                description= club.DESCRIPTION if club.DESCRIPTION is not None else "",
                image=f"{host}/{image_path}",
                member=member,
                total_distance=round(club.CLUB_TOTAL_DISTANCE, 2) if club.CLUB_TOTAL_DISTANCE is not None else 0 
            )
            all_club_info.append(club_data)
        total_page = ceil(total_club / per_page)
        return ClubsResponse(
            per_page=per_page,
            current_page=current_page,
            total_page=total_page,
            total_club=total_club,
            clubs=all_club_info,
        )
    except Exception:
        raise HTTPException(status_code=500 ,detail="Lỗi hiển thị danh sách các câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# Get the club details no acc
def get_club_details(host: str, club_id: int,
                     db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()

    try:
        total_member_in_club = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        admin_user = db.query(User).filter(User.USER_ID == club.ADMIN).first()
        # Trả về Response Club Detail cho Front End
        image_path = club.PICTURE_PATH.replace("\\", "/")
        detail_club=DetailClub(
            club_id=club.CLUB_ID,
            club_name=club.CLUB_NAME,
            club_image=f"{host}/{image_path}",
            club_slogan=club.DESCRIPTION or "Mobirace Forever",
            total_member=total_member_in_club,
            total_distance=round(club.CLUB_TOTAL_DISTANCE or 0, 2),
            founding_date = club.CREATE_AT.strftime('%d/%m/%Y %H:%M:%S'),     
            club_name_admin=admin_user.FULL_NAME if admin_user else None,
            min_pace=club.MIN_PACE,
            max_pace=club.MAX_PACE,
            )
        return {"data":detail_club}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#Search club by name
def get_club_by_clubname(host: str, search :str, per_page : int, current_page : int, db: Session):
    try:
        skip = (current_page - 1) * per_page
        clubs = db.query(Club, func.count(User_Club.c.USER_ID)).\
            outerjoin(User_Club, Club.CLUB_ID == User_Club.c.CLUB_ID).\
            filter(Club.CLUB_NAME.ilike(f"%{search}%")).\
            group_by(Club.CLUB_ID)
        total_clubs = clubs.count()
        clubs = clubs.offset(skip).limit(per_page).all()
        all_club_info = []
        for club, member_count in clubs:
            description = club.DESCRIPTION if club.DESCRIPTION is not None else ""
            image_path = club.PICTURE_PATH.replace("\\", "/")
            club_data = ClubBase(
                id=club.CLUB_ID,
                name=club.CLUB_NAME,
                description=description,
                image=f"{host}/{image_path}",
                member=member_count,
                total_distance=round(club.CLUB_TOTAL_DISTANCE or 0,1),
            )
            all_club_info.append(club_data)
        total_page = ceil(total_clubs / per_page)
        return ClubsResponse(
            per_page=per_page,
            current_page=current_page,
            total_page=total_page,
            total_club=total_clubs,
            clubs=all_club_info
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi tìm kiếm câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

create_club_semaphore = threading.Semaphore(1)
#Tạo club mới
def create_club(db: Session, current_user: User,
                title: str = Form(...),
                content: Optional[str] = Form(None),
                image: Union[UploadFile,str] = Form(None),
                min_pace: Optional[float]=Form(None),
                max_pace: Optional[float]=Form(None) ):
    with create_club_semaphore:
        existing_club = db.query(Club).filter(Club.CLUB_NAME == title).first()
        if existing_club:
            raise HTTPException(status_code=400, detail="Câu lạc bộ đã tồn tại")
        if image != 'null': 
            formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename= f"club_add_{formatted_date}.jpg"

            with open(os.path.join("images", filename), "wb") as f:
                shutil.copyfileobj(image.file, f)

            image_path = os.path.join('images', filename)

            add_club = Club(
                CLUB_NAME=title,
                DESCRIPTION=content,
                PICTURE_PATH=image_path,
                ADMIN=current_user.USER_ID,
                MIN_PACE=min_pace,
                MAX_PACE=max_pace,
                CREATOR_ID=current_user.USER_ID
            )
            db.add(add_club)
            db.commit()
            db.refresh(add_club)
            update_club_ranking(db)
            return {"status": 200, "detail": "Tạo câu lạc bộ thành công"}
        else:
            raise HTTPException(status_code=422, detail="Vui lòng chọn hình ảnh cho câu lạc bộ!")
         
# Thêm user vào club
def join_club(club_id: int, current_user: User, db: Session):
    try:
        existing_user_club = db.query(User_Club).filter(User_Club.c.USER_ID == current_user.USER_ID, User_Club.c.CLUB_ID == club_id).first()
        if existing_user_club:
            raise HTTPException(status_code=200, detail="Bạn đã tham gia câu lạc bộ này")
        club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
        new_user_club = User_Club.insert().values(
            USER_ID=current_user.USER_ID,
            CLUB_ID=club_id,
            JOIN_DATE=datetime.now(),
            TOTAL_DISTANCE=0.0
        )
        db.execute(new_user_club)
        sync_runs_to_user_club_activity(db)
        update_user_club_distance_and_pace(db)
        calculate_club_total_distance(db)
        update_user_club_ranking(db)
        update_club_ranking(db)
        db.commit()
        return {"status": 200, "detail": "Tham gia câu lạc bộ thành công"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi thao tác tham gia câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# User thoát club
def leave_club(club_id: int, current_user: User, db: Session):
    user_club = db.query(User_Club).filter(
            User_Club.c.USER_ID == current_user.USER_ID,
            User_Club.c.CLUB_ID == club_id
        ).first()
    if not user_club:
        raise HTTPException(status_code=400, detail="Bạn chưa tham gia câu lạc bộ này")
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if club.ADMIN == current_user.USER_ID:
        raise HTTPException(status_code=400, detail="Không thể rời câu lạc bộ khi bạn là admin")
    try:
        db.query(User_Club_Activity).filter(User_Club_Activity.CLUB_ID == club_id, User_Club_Activity.USER_ID == current_user.USER_ID).delete()
        db.execute(User_Club.delete().where(
            (User_Club.c.USER_ID == current_user.USER_ID) &
            (User_Club.c.CLUB_ID == club_id)
        ))

        db.commit()
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        return {"status": 200, "detail": "Thao tác thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hủy tham gian câu lạc bộ thất bại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#cập nhật club
def update_club(db: Session, 
                club_id: int,
                title: str = Form(...),
                content: Optional[str] = Form(None),
                image: Union[UploadFile,str] = Form(None),
                min_pace: Optional[float]=Form(None),
                max_pace: Optional[float]=Form(None)):
    
    existing_club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if not existing_club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    
    try:
        old_image_path = existing_club.PICTURE_PATH
        if image != 'null':
            formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename= f"club_add_{formatted_date}.jpg"

            with open(os.path.join("images", filename), "wb") as f:
                shutil.copyfileobj(image.file, f)

            image_path_new = os.path.join('images', filename)

            update_data = {
                "CLUB_NAME": title,
                "DESCRIPTION": content,
                "PICTURE_PATH": image_path_new,
                "MIN_PACE": min_pace,
                "MAX_PACE": max_pace
            }
            if old_image_path and  os.path.exists(old_image_path):
                old_image_filename = os.path.basename(old_image_path)
                if old_image_filename:
                        os.remove(old_image_path)

            db.query(Club).filter(Club.CLUB_ID == club_id).update(update_data)
            db.commit()
            db.close()
        else: 
            update_data = {
                "CLUB_NAME": title,
                "DESCRIPTION": content,
                "PICTURE_PATH": existing_club.PICTURE_PATH,
                "MIN_PACE": min_pace,
                "MAX_PACE": max_pace
            }

            db.query(Club).filter(Club.CLUB_ID == club_id).update(update_data)
            db.commit()
            db.close()
        
        return {"status": 200, "detail": "Cập nhật thông tin câu lạc bộ thành công"}
    except Exception as e:
        db.rollback()
        db.close()
        raise HTTPException(status_code=400, detail="Cập nhật thông tin thất bại")

# xóa club
def delete_club(club_id: int, db: Session):
    existing_club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if not existing_club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    try:
        old_image_path = existing_club.PICTURE_PATH
        if old_image_path and  os.path.exists(old_image_path):
                old_image_filename = os.path.basename(old_image_path)
                if old_image_filename:
                        os.remove(old_image_path)
        db.query(User_Club_Activity).filter(User_Club_Activity.CLUB_ID == club_id).delete()
        db.query(User_Club).filter(User_Club.c.CLUB_ID == club_id).delete()
        db.delete(existing_club)
        db.commit() 
        update_club_ranking(db)
        return {"status": 200, "detail": "Xóa câu lạc bộ thành công"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Xóa câu lạc bộ không thành công! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# xóa user khỏi club
def remove_user_from_club(user_id: int, club_id: int, db: Session, current_user: User):
    if user_id == current_user.USER_ID:
        raise HTTPException(status_code=400, detail="Bạn không thể tự xóa chính mình khỏi câu lạc bộ")

    user_club_delete = (
        delete(User_Club)
        .where(User_Club.c.USER_ID == user_id)
        .where(User_Club.c.CLUB_ID == club_id)
    )
    deleted_count = db.execute(user_club_delete).rowcount
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng trong câu lạc bộ")
    db.commit()
    update_user_club_ranking(db)
    calculate_club_total_distance(db)
    update_club_ranking(db)
    return {"status": 200, "detail": "Xóa thành viên thành công"}

def get_club_info(clubs_query: List[Club], per_page: int, current_page: int) -> List[Dict]:
    clubs = clubs_query.offset((current_page - 1) * per_page).limit(per_page).all()
    club_info = [
        {
            "club_id": club.CLUB_ID,
            "club_name": club.CLUB_NAME,
            "club_image": club.PICTURE_PATH,
            "club_description": club.DESCRIPTION,
            "admin_user_id": club.admin_user.USER_ID,  
            "admin_user_name": club.admin_user.FULL_NAME
        }
        for club in clubs
    ]
    return club_info

#get my club
def get_user_clubs(host: str, db: Session, current_user: User, current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page')) -> Dict:
    user_club_ids = (
        db.query(User_Club.c.CLUB_ID)
        .filter(User_Club.c.USER_ID == current_user.USER_ID)
    ).subquery()
    admin_club_ids = (
        db.query(Club.CLUB_ID)
        .filter(Club.ADMIN == current_user.USER_ID)
    ).subquery()
    clubs_query = (
        db.query(Club, User.FULL_NAME.label("admin_user_name"))  
        .join(User, Club.ADMIN == User.USER_ID, isouter=True)
        .outerjoin(user_club_ids, Club.CLUB_ID == user_club_ids.c.CLUB_ID)
        .outerjoin(admin_club_ids, Club.CLUB_ID == admin_club_ids.c.CLUB_ID)
        .filter(or_(user_club_ids.c.CLUB_ID.isnot(None), admin_club_ids.c.CLUB_ID.isnot(None)))
        .offset((current_page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    if not clubs_query:  
        return {"join_club": False}
    club_info = [
        {
            "club_id": club.Club.CLUB_ID,
            "club_name": club.Club.CLUB_NAME,
            "club_image": f"{host}/{club.Club.PICTURE_PATH}",
            "club_description": club.Club.DESCRIPTION,
            "admin_user_name": club.admin_user_name,
        }
        for club in clubs_query
    ]
    total_clubs_query = (
        db.query(Club)
        .outerjoin(user_club_ids, Club.CLUB_ID == user_club_ids.c.CLUB_ID)
        .outerjoin(admin_club_ids, Club.CLUB_ID == admin_club_ids.c.CLUB_ID)
        .filter(or_(user_club_ids.c.CLUB_ID.isnot(None), admin_club_ids.c.CLUB_ID.isnot(None)))
    )
    total_clubs = total_clubs_query.count()
    total_pages = (total_clubs + per_page - 1) // per_page
    return {
        "join_club": True,
        "per_page": per_page,
        "current_page": current_page,
        "total_page": total_pages,
        "total_club": total_clubs,
        "list_clubs": {
            "clubs": club_info,
        }
    }

def is_user_or_admin(user_id: int, club_id: int, db: Session) -> str:
    admin_club = db.query(Club.ADMIN).filter(Club.CLUB_ID == club_id).scalar()
    
    if user_id == admin_club:
        return "admin"
    
    user_in_club = db.query(User_Club).filter(
        User_Club.c.USER_ID == user_id,
        User_Club.c.CLUB_ID == club_id
    ).one_or_none()
    
    if user_in_club:
        return "member"
    else:
        return "non_member"

# detail club có acc    
def get_detail_club(host: str, club_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    user_status = is_user_or_admin(current_user.USER_ID, club_id, db)

    try:
    
        total_member_in_club = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        admin_user = db.query(User).filter(User.USER_ID == club.ADMIN).first()

        image_path = club.PICTURE_PATH.replace("\\", "/")
        myclub=DetailClubFor(
            club_id=club.CLUB_ID,
            club_name=club.CLUB_NAME,
            club_image=f"{host}/{image_path}",
            club_slogan=club.DESCRIPTION or "Mobirace Forever",
            total_member=total_member_in_club,
            total_distance=round(club.CLUB_TOTAL_DISTANCE or 0, 2),
            founding_date=club.CREATE_AT.strftime('%d/%m/%Y %H:%M:%S'),
            club_name_admin=admin_user.FULL_NAME if admin_user else None,
            is_admin=user_status == "admin",
            user_status=user_status,
            min_pace=club.MIN_PACE,
            max_pace=club.MAX_PACE
        )

        return myclub
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# detail club có acc    
def get_detail_club_1(host: str, club_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    user_status = is_user_or_admin(current_user.USER_ID, club_id, db)

    try:
    
        total_member_in_club = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        admin_user = db.query(User).filter(User.USER_ID == club.ADMIN).first()

        image_path = club.PICTURE_PATH.replace("\\", "/")
        myclub=DetailClubFor(
            club_id=club.CLUB_ID,
            club_name=club.CLUB_NAME,
            club_image=f"{host}/{image_path}",
            club_slogan=club.DESCRIPTION or "Mobirace Forever",
            total_member=total_member_in_club,
            total_distance=round(club.CLUB_TOTAL_DISTANCE or 0, 2),
            founding_date=club.CREATE_AT.strftime('%d/%m/%Y %H:%M:%S'),
            club_name_admin=admin_user.FULL_NAME if admin_user else None,
            is_admin=user_status == "admin",
            user_status=user_status,
            min_pace=club.MIN_PACE,
            max_pace=club.MAX_PACE
        )

        return { "data": myclub}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def change_admin_club(request:Change_admin, db:Session, current_user:User):
    club = db.query(Club).filter(Club.CLUB_ID == request.club_id, Club.ADMIN == current_user.USER_ID).first()
    if not club:
        raise HTTPException(status_code=404, detail="Câu lạc bồ không tồn tại!")
    
    new_admin = db.query(User).filter(User.USER_ID == request.admin_id).one_or_none()
    if not new_admin:
        raise HTTPException(status_code=404, detail="Người dùng mới không tồn tại!")
    try:
        # Cập nhật admin của club
        club.ADMIN = request.admin_id
        db.commit()
        return {"message": "Thay đổi admin thành công", "status_code": 200} 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Đổi admin thất bại! Vui lòng liên hệ  quản trị hệ thống để hỗ trợ!")
    
from sqlalchemy import and_

def get_active_user_club(club_id: int, user_id: int, db: Session):
    user_club_join_date = db.query(User_Club.c.JOIN_DATE) \
        .filter(User_Club.c.CLUB_ID == club_id) \
        .filter(User_Club.c.USER_ID == user_id) \
        .scalar()

    if not user_club_join_date:
        return []

    query = db.query(User_Club.c.TOTAL_DISTANCE, User_Club.c.PACE, Run.RUN_ID, Run.DISTANCE, Run.PACE, Run.DURATION, Run.NAME, Run.CREATED_AT) \
        .join(Run, (User_Club.c.USER_ID == Run.USER_ID)) \
        .filter(User_Club.c.CLUB_ID == club_id) \
        .filter(User_Club.c.USER_ID == user_id) \
        .filter(User_Club.c.USER_ID == Run.USER_ID) \
        .filter(Run.CREATED_AT > user_club_join_date) \
        .all()

    active_user_club = []

    for row in query:
        total_distance, pace, run_id, run_distance, run_pace, run_duration, run_name, created_at = row
        member_info = {
            "activate_id": run_id,
            "datetime": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "member_distance":run_distance,
            "member_pace": run_pace,
            "member_duration": run_duration,
            "activate_name": run_name,
        }
        active_user_club.append(member_info)

    return active_user_club

def search_club_members(club_id: int, search: str, month: Optional[int] = None,
                     current_page: int = Query(1, alias='current_page'),
                     per_page: int = Query(10, alias='per_page'),
                     db: Session = Depends(get_db)):
    detail_club_response = get_club_details(club_id, month, current_page, per_page, db)
    filtered_members = [member for member in detail_club_response.members if search.replace(" ", "").lower() in member.member_name.replace(" ", "").lower()]

    total_member = len(filtered_members)
    total_pages = ceil(total_member / per_page)

    search_member_response = SearchMemberInClub(
        per_page=per_page,
        total_member=total_member,
        current_page=current_page,
        total_page=total_pages,
        members=filtered_members
    )
    return search_member_response

def get_user_club_activity(user_id: int, club_id: int, db: Session):
    try:
        # Lấy thông tin user_event_activity dựa trên user_id và event_id
        activity = db.query(User_Club_Activity).filter(
            User_Club_Activity.USER_ID == user_id,
            User_Club_Activity.CLUB_ID == club_id,
            # User_Club_Activity.STATUS== 1
        ).all()

        if not activity:
            raise HTTPException(status_code=404, detail="User club activity not found")
        for res in activity:
            res.CREATED_AT = res.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S")
        return activity

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def hide_activity_in_club(run_id: int ,club_id: int,reason:str,db: Session,current_user:User):
    try:
        admin=db.query(Club).filter(Club.ADMIN==current_user.USER_ID).first()
        if not admin:
            raise HTTPException(status_code=404,detail="bạn không phải Admin của CLB này")
        # Lấy thông tin user_event_activity dựa trên run_id và event_id
        activity = db.query(User_Club_Activity).filter(
            User_Club_Activity.RUN_ID == run_id,
            User_Club_Activity.CLUB_ID == club_id,
            User_Club_Activity.STATUS == 1
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity in event not found")

        # Đặt STATUS = 0 để ẩn hoạt động
        activity.STATUS = 0
        activity.REASON=reason
        db.commit()
        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        update_user_ranking(db)
        update_ranking_event(db)

        return {"message": "Activity in event hidden successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

def re_hide_activity_in_club(run_id: int ,club_id: int,db: Session,current_user:User):
    try:
        admin=db.query(Club).filter(Club.ADMIN==current_user.USER_ID).first()
        if not admin:
            raise HTTPException(status_code=404,detail="bạn không phải Admin của CLB này")
        # Lấy thông tin user_event_activity dựa trên run_id và event_id
        activity = db.query(User_Club_Activity).filter(
            User_Club_Activity.RUN_ID == run_id,
            User_Club_Activity.CLUB_ID == club_id,
            User_Club_Activity.STATUS == 0
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity in event not found")

        # Đặt STATUS = 0 để không ẩn hoạt động
        activity.STATUS = 1
        activity.REASON=None
        db.commit()
        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        update_user_ranking(db)
        update_ranking_event(db)

        return {"message": "Activity in event hidden successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()
        
def get_user_club_activity_by_date(user_id: int, club_id: int, db: Session, textSearch: str = None):
    try:
        query = db.query(User_Club_Activity).filter(
            User_Club_Activity.USER_ID == user_id,
            User_Club_Activity.CLUB_ID == club_id
        )

        activity = query.all()

        if not activity:
            raise HTTPException(status_code=404, detail="User event activity not found")

        for res in activity:
            res.CREATED_AT = res.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S")

        if textSearch:
            filtered_activity = [
                res for res in activity if res.CREATED_AT.startswith(textSearch)
            ]
            return filtered_activity

        return activity

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Hàm hiển thị danh sách thành viên của Club tung.nguyenson11 28/09/2023
def get_members_club(host: str, 
                     club_id: int, 
                     month: Optional[int] = None,
                     year: Optional[int] = None,
                     search_name: Optional[str] = None,
                     current_page: int = Query(1, alias='current_page'),
                     per_page: int = Query(10, alias='per_page'),
                     db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if club is None:
        raise HTTPException(status_code=404, detail="câu lạc bộ không tồn tại!")
    try:
        members_query = db.query(User.USER_ID.label("user_id"),
                            func.sum(User_Club_Activity.DISTANCE).label("member_distance"),
                            func.avg(User_Club_Activity.PACE).label("member_pace"),
                            User_Club.c.RANKING.label("member_rank")) \
                        .outerjoin(User_Club, User.USER_ID == User_Club.c.USER_ID) \
                        .outerjoin(User_Club_Activity, and_(User_Club_Activity.USER_ID == User.USER_ID,
                                                            # can.lt comment 14/10/23
                                                            # User_Club_Activity.CREATED_AT >= User_Club.c.JOIN_DATE,
                                                            User_Club_Activity.STATUS == '1')) \
                        .filter(User_Club.c.CLUB_ID == club_id) \
                        .group_by(User.USER_ID)
        
        total_record  = len(members_query.all())
        
        if month and year:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            members_query = members_query.filter(User_Club_Activity.CREATED_AT >= start_date,
                                                User_Club_Activity.CREATED_AT <= end_date)
            total_record  = len(members_query.all())
            
        # Xem chi tiết câu lạc bộ theo tìm kiếm tên thành viên:    
        if (search_name != 'undefined' and search_name !='') and search_name is not None:
            members_query = members_query.filter(User.FULL_NAME.ilike(f"%{search_name}%"))
            total_record  = len(members_query.all())
        
        # Hiển thị danh sách thành viên của câu lạc bộ
        members_query = members_query.order_by(desc("member_distance"), "member_rank") \
                        .limit(per_page).offset((current_page - 1) * per_page)

        members_results = members_query.all()

        ranked_members = []
        rank = 1
        
        for result in members_results:
            user_id, member_distance, member_pace, member_rank = result
            user = db.query(User).filter(User.USER_ID == user_id).first()
            image_path_user = user.AVATAR_PATH.replace("\\", "/")
            member_join_date = db.query(User_Club.c.JOIN_DATE).filter((User_Club.c.CLUB_ID == club_id) & (User_Club.c.USER_ID == user_id)).first()
            
            ranked_members.append(
                Member(member_id=user.USER_ID,
                    member_name=user.FULL_NAME,
                    member_join_date=member_join_date[0].strftime('%d/%m/%Y %H:%M:%S'),
                    member_rank=member_rank,
                    member_image=f"{host}/{image_path_user}",
                    member_distance=round(member_distance or 0, 2),                
                    member_pace=format_seconds(int((member_pace if member_pace is not None else 0) * 60)),
                    member_gender=user.GENDER)
            )
            rank += 1
        
        # total_member = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        total_member = total_record
        total_pages = ceil(total_member / per_page)

        return {
            "ranked_members": ranked_members,
            "per_page":per_page,
            "current_page":current_page,
            "total_record":total_member
            # "total_pages":total_pages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# Hàm hiển thị tất cả hoạt động chạy trong câu lạc bộ tung.nguyenson11 28/09/2023
def get_new_activities_club(host: str, club_id: int, 
                            hour: Optional[int] = 48,
                            search_name: Optional[str] = None,
                            current_page: int = Query(1, alias='current_page'),
                            per_page: int = Query(10, alias='per_page'),
                            db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if club is None:
        raise HTTPException(status_code=404,detail="Câu lạc bộ không tồn tại!")
    try:
        # start_time = datetime.now() - timedelta(hours=48)
        start_time = datetime.now() - timedelta(hours=hour)
        latest_activates = db.query(Run).join(User, Run.USER_ID == User.USER_ID) \
            .filter(Run.USER_ID == User_Club.c.USER_ID) \
            .filter(User_Club.c.CLUB_ID == club_id) \
            .filter(Run.CREATED_AT >= start_time)
        
            # can.lt comment 14/10/23
            # .filter(Run.CREATED_AT >= User_Club.c.JOIN_DATE) 
            

        # Hiển thị danh sách các hoạt động theo tìm kiếm tên thành viên trong câu lạc bộ
        if search_name != 'undefined' and search_name != '':
            latest_activates = latest_activates.filter(User.FULL_NAME.ilike(f"%{search_name}%"))

        latest_activates = latest_activates.order_by(desc(Run.CREATED_AT)) \
                                            .limit(per_page) \
                                            .offset((current_page - 1) * per_page).all()
                    
        # user_ids = [activate.USER_ID for activate in latest_activates]
        # user_names = db.query(User.USER_ID, User.FULL_NAME).filter(User.USER_ID.in_(user_ids)).all()
        # user_avatars = db.query(User.USER_ID, User.AVATAR_PATH).filter(User.USER_ID.in_(user_ids)).all()
        # user_name_dict = {user_id: user_name for user_id, user_name in user_names}
        # user_avatar_dict = {user_id: avatar for user_id, avatar in user_avatars}

        # new_activates = [NewActivate(active_id=activate.RUN_ID,
        #                             member_id=activate.USER_ID,
        #                             member_avatar=f"{host}/{user_avatar_dict[activate.USER_ID]}",
        #                             datetime=activate.CREATED_AT.strftime('%Y-%m-%d %H:%M:%S'),
        #                             member_name=user_name_dict[activate.USER_ID],
        #                             member_distance=round(activate.DISTANCE or 0, 2), 
        #                             # member_pace = round(activate.PACE or 0, 2),
        #                             member_pace = format_seconds(int(activate.PACE * 60)) if activate.PACE else "00:00:00",
        #                             member_duration=activate.DURATION,
        #                             activate_name=activate.NAME,
        #                             activate_type=activate.TYPE,
        #                             activity_link_strava=activate.STRAVA_RUN_ID,
        #                             activity_map=activate.SUMMARY_POLYLINE) for activate in latest_activates]
        user_ids = [activate.USER_ID for activate in latest_activates]
        run_ids = [activate.RUN_ID for activate in latest_activates]
        user_names = db.query(User.USER_ID, User.FULL_NAME).filter(User.USER_ID.in_(user_ids)).all()
        user_avatars = db.query(User.USER_ID, User.AVATAR_PATH).filter(User.USER_ID.in_(user_ids)).all()
        user_strava_run_ids = db.query(Run.RUN_ID, Run.STRAVA_RUN_ID).filter(Run.RUN_ID.in_(run_ids)).all()
        user_map_ids = db.query(Run.RUN_ID, Run.SUMMARY_POLYLINE).filter(Run.RUN_ID.in_(run_ids)).all()
        user_type_ids = db.query(Run.RUN_ID, Run.TYPE).filter(Run.RUN_ID.in_(run_ids)).all()
        user_name_dict = {user_id: user_name for user_id, user_name in user_names}
        user_avatar_dict = {user_id: avatar for user_id, avatar in user_avatars}
        user_strava_run_id_dict = {run_id: strava_run_id for run_id, strava_run_id in user_strava_run_ids}
        user_map_dict = {run_id: summarry_polyline for run_id, summarry_polyline in user_map_ids}
        user_type_dict = {run_id: type for run_id, type in user_type_ids}

        new_activates = [NewActivate(activity_id=activate.RUN_ID,
                                    member_id=activate.USER_ID,
                                    member_avatar=f"{host}/{user_avatar_dict[activate.USER_ID]}",
                                    activity_start_date=activate.CREATED_AT.strftime('%d/%m/%Y %H:%M:%S'),
                                    member_name=user_name_dict[activate.USER_ID],
                                    activity_distance=round(activate.DISTANCE or 0, 2), 
                                    activity_pace = format_seconds(int(activate.PACE * 60)) if activate.PACE else "00:00:00",
                                    activity_name=activate.NAME,
                                    activity_type=user_type_dict[activate.RUN_ID], #
                                    activity_link_strava=user_strava_run_id_dict[activate.RUN_ID],
                                    activity_map=user_map_dict[activate.RUN_ID],
                                    status=activate.STATUS,
                                    reason=activate.REASON) for activate in latest_activates]
        total_activities = db.query(func.count(Run.RUN_ID)).join(User, Run.USER_ID == User.USER_ID) \
                                                .filter(Run.USER_ID == User_Club.c.USER_ID) \
                                                .filter(User_Club.c.CLUB_ID == club_id) \
                                                .filter(Run.CREATED_AT >= start_time).scalar()
                                                # can.lt comment 14/10/23
                                                #.filter(Run.CREATED_AT >= User_Club.c.JOIN_DATE) \
        total_pages=ceil(total_activities / per_page)

        return {
            "new_activities":new_activates,
            "per_page":per_page,
            "current_page":current_page,
            "total_activates":total_activities,
            "total_pages":total_pages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị danh sách hoạt động câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#can.lt 14/10/23
def deactive_activity(payload: FraudulentActivity, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.RUN_ID == payload.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động")
    club = db.query(Club).filter(Club.CLUB_ID == payload.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    if payload.user_id != club.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")
    
    # Kiểm tra xem dữ liệu đã tồn tại hay chưa
    existing_data = db.query(Flaudulent_Activity_Club).filter(
        Flaudulent_Activity_Club.CLUB_ID == payload.club_id,
        Flaudulent_Activity_Club.ACTIVITY_ID == run.STRAVA_RUN_ID
    ).first()
    if existing_data:
        raise HTTPException(status_code=409, detail="Dữ liệu đã tồn tại")

    # Tạo dữ liệu mới
    new_data = Flaudulent_Activity_Club(
        CREATED_ID = payload.user_id,
        CLUB_ID = payload.club_id,
        ACTIVITY_ID = run.STRAVA_RUN_ID,
        REASON = payload.reason,
        CREATE_DATETIME = datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_data)
    db.query(User_Club_Activity).filter(
        User_Club_Activity.CLUB_ID == payload.club_id,
        User_Club_Activity.RUN_ID == payload.run_id
    ).update({"STATUS": 0})
    sync_runs_to_user_club_activity(db, payload.club_id, False)
    update_user_club_distance_and_pace(db, payload.club_id)
    calculate_club_total_distance(db, payload.club_id)
    update_user_club_ranking(db, payload.club_id)
    update_club_ranking(db, payload.club_id)
    db.commit()
    return {"status_code": 200, "detail": "Hủy bỏ dữ liệu chạy thành công"}

#can.lt 14/10/23
def active_activity(payload: FraudulentActivity, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.RUN_ID == payload.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động")
    club = db.query(Club).filter(Club.CLUB_ID == payload.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    if payload.user_id != club.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")
    
    # Xóa dữ liệu gian lận
    record = db.query(Flaudulent_Activity_Club).filter(
        Flaudulent_Activity_Club.CLUB_ID == payload.club_id,
        Flaudulent_Activity_Club.ACTIVITY_ID == run.STRAVA_RUN_ID
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu gian lận")
    db.delete(record)
    # active lại dữ liệu chạy
    db.query(User_Club_Activity).filter(
        User_Club_Activity.CLUB_ID == payload.club_id,
        User_Club_Activity.RUN_ID == payload.run_id
    ).update({"STATUS": 1})
    sync_runs_to_user_club_activity(db, payload.club_id, False)
    update_user_club_distance_and_pace(db, payload.club_id)
    calculate_club_total_distance(db, payload.club_id)
    update_user_club_ranking(db, payload.club_id)
    update_club_ranking(db, payload.club_id)
    db.commit()
    return {"status_code": 200, "detail": "Kích hoạt lại dữ liệu chạy thành công"}

#test hàm
# Hàm hiển thị tất cả hoạt động chạy trong câu lạc bộ tung.nguyenson11 28/09/2023
def get_new_activities_club_main(host: str, club_id: int, 
                            hour: Optional[int] = 48,
                            search_name: Optional[str] = None,
                            current_page: int = Query(1, alias='current_page'),
                            per_page: int = Query(10, alias='per_page'),
                            db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if club is None:
        raise HTTPException(status_code=404,detail="Câu lạc bộ không tồn tại!")
    try:
        start_time = datetime.now() - timedelta(hours=hour)
        latest_activates = db.query(User_Club_Activity).join(User, User_Club_Activity.USER_ID == User.USER_ID) \
                .filter(User_Club_Activity.USER_ID == User_Club.c.USER_ID) \
                .filter(User_Club.c.CLUB_ID == club_id) \
                .filter(User_Club_Activity.STATUS == "1") \
                .filter(User_Club_Activity.CREATED_AT >= start_time)  
            # can.lt comment 14/10/23
            # .filter(Run.CREATED_AT >= User_Club.c.JOIN_DATE) 
        total_record  = len(latest_activates.all())
        
        # Hiển thị danh sách các hoạt động theo tìm kiếm tên thành viên trong câu lạc bộ
        if (search_name != 'undefined' and search_name !='') and search_name is not None:
            latest_activates = latest_activates \
                                .filter(or_(
                                            User_Club_Activity.NAME.ilike(f"%{search_name}%"),
                                            User.FULL_NAME.ilike(f"%{search_name}%")
                                        ))
                                # .filter(User_Club_Activity.NAME.ilike(f"%{search_name}%") or User.FULL_NAME.ilike(f"%{search_name}%"))
            total_record  = len(latest_activates.all())

        latest_activates = latest_activates.order_by(desc(User_Club_Activity.CREATED_AT)) \
                                            .limit(per_page).offset((current_page - 1) * per_page).all()
                    
        user_ids = [activate.USER_ID for activate in latest_activates]
        run_ids = [activate.RUN_ID for activate in latest_activates]
        user_names = db.query(User.USER_ID, User.FULL_NAME).filter(User.USER_ID.in_(user_ids)).all()
        user_avatars = db.query(User.USER_ID, User.AVATAR_PATH).filter(User.USER_ID.in_(user_ids)).all()
        user_strava_run_ids = db.query(Run.RUN_ID, Run.STRAVA_RUN_ID).filter(Run.RUN_ID.in_(run_ids)).all()
        user_map_ids = db.query(Run.RUN_ID, Run.SUMMARY_POLYLINE).filter(Run.RUN_ID.in_(run_ids)).all()
        user_type_ids = db.query(Run.RUN_ID, Run.TYPE).filter(Run.RUN_ID.in_(run_ids)).all()
        durations_info = db.query(Run.RUN_ID, Run.DURATION).filter(Run.RUN_ID.in_(run_ids)).all()

        user_name_dict = {user_id: user_name for user_id, user_name in user_names}
        user_avatar_dict = {user_id: avatar for user_id, avatar in user_avatars}
        user_strava_run_id_dict = {run_id: strava_run_id for run_id, strava_run_id in user_strava_run_ids}
        user_map_dict = {run_id: summarry_polyline for run_id, summarry_polyline in user_map_ids}
        user_type_dict = {run_id: type for run_id, type in user_type_ids}
        duration = {run_id: duration for run_id, duration in durations_info}

        new_activates = [NewActivate(activity_id=activate.RUN_ID,
                                    member_id=activate.USER_ID,
                                    member_avatar=f"{host}/{user_avatar_dict[activate.USER_ID]}",
                                    activity_start_date=activate.CREATED_AT.strftime('%d/%m/%Y %H:%M:%S'),
                                    member_name=user_name_dict[activate.USER_ID],
                                    activity_distance=round(activate.DISTANCE or 0, 2), 
                                    activity_pace = format_seconds(int(activate.PACE * 60)) if activate.PACE else "00:00:00",
                                    activity_name=activate.NAME,
                                    activity_type=user_type_dict[activate.RUN_ID], #
                                    activity_link_strava=user_strava_run_id_dict[activate.RUN_ID],
                                    activity_map=user_map_dict[activate.RUN_ID],
                                    activity_finish=duration[activate.RUN_ID],
                                    status=activate.STATUS,
                                    reason=activate.REASON) for activate in latest_activates]
        total_activities = total_record

        return {
            "detail":new_activates,
            "per_page":per_page,
            "current_page":current_page,
            "total_record":total_activities
            # "total_pages":total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị danh sách hoạt động câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#hàm lấy ra chi tiết thông tin thành viên trong câu lạc bộ tung.nguyenson11 28/09/2023
def get_detail_member_club(host: str, club_id: int,
                            member_id: int,
                            db: Session = Depends(get_db),
                            user_id: Optional[int] = None):
    
    club = db.query(Club).filter(Club.CLUB_ID == club_id).one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    user_status = ""
    if user_id is not None:
        user_status = is_user_or_admin(user_id, club_id, db)
    member_detail = db.query(User_Club).filter(User_Club.c.CLUB_ID == club_id, User_Club.c.USER_ID == member_id).first()
    total_run = db.query(func.count(User_Club_Activity.RUN_ID)) \
                  .filter(User_Club_Activity.USER_ID == member_id, User_Club_Activity.CLUB_ID == club_id) \
                  .group_by(User_Club_Activity.USER_ID == member_id, User_Club_Activity.CLUB_ID == club_id).scalar()
    if member_detail is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên này trong câu lạc bộ")
    try:
        user = db.query(User).filter(User.USER_ID == member_detail.USER_ID).first()

        image_path = user.AVATAR_PATH.replace("\\", "/")
        myclub={       
                "user_id": member_id,
                "fullname": user.FULL_NAME,
                "image" : f"{host}/{image_path}",
                "total_distance" : round(member_detail.TOTAL_DISTANCE,2) if member_detail.TOTAL_DISTANCE else 0,
                "avg_pace" : format_seconds(int(member_detail.PACE * 60)) if member_detail.PACE else "00:00:00",
                "total_run" : total_run,
                "strava_user_link": user.STRAVA_ID,
                'is_admin': user_status == "admin",
        }

        return myclub
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết thành viên câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#Hàm hiển thị chi tiết câu lạc bộ khi chưa đăng nhập tung.nguyenson 15/10/2023
def get_detail_club_no_acc(host: str, club_id: int,
                        db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    try:
    
        total_member_in_club = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        admin_user = db.query(User).filter(User.USER_ID == club.ADMIN).first()

        image_path = club.PICTURE_PATH.replace("\\", "/")

        myClub={
            "club_id": club.CLUB_ID,
            "club_name": club.CLUB_NAME,
            "club_image": f"{host}/{image_path}",
            "club_slogan": club.DESCRIPTION or "Mobirace Forever",
            "total_member": total_member_in_club,
            "total_distance": round(club.CLUB_TOTAL_DISTANCE or 0, 2),
            "founding_date": club.CREATE_AT.strftime('%d/%m/%Y %H:%M:%S'),
            "club_name_admin": admin_user.FULL_NAME if admin_user else None,
            "is_admin": False,
            "user_status": "",
            "min_pace": club.MIN_PACE,
            "max_pace": club.MAX_PACE
        }

        return myClub
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#Hàm hiển thị danh sách thành viên của Club tung.nguyenson11 28/09/2023
def get_members_club_1(host: str, 
                     club_id: int, 
                     month: Optional[int] = None,
                     year: Optional[int] = None,
                     search_name: Optional[str] = None,
                     current_page: int = Query(1, alias='current_page'),
                     per_page: int = Query(10, alias='per_page'),
                     db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).first()
    if club is None:
        raise HTTPException(status_code=404, detail="câu lạc bộ không tồn tại!")
    try:
        members_query = db.query(User.USER_ID.label("user_id"),
                            func.sum(User_Club_Activity.DISTANCE).label("member_distance"),
                            func.avg(User_Club_Activity.PACE).label("member_pace"),
                            User_Club.c.RANKING.label("member_rank")) \
                        .outerjoin(User_Club, User.USER_ID == User_Club.c.USER_ID) \
                        .outerjoin(User_Club_Activity, and_(User_Club_Activity.USER_ID == User.USER_ID,
                                                            # can.lt comment 14/10/23
                                                            # User_Club_Activity.CREATED_AT >= User_Club.c.JOIN_DATE,
                                                            User_Club_Activity.STATUS == '1')) \
                        .filter(User_Club.c.CLUB_ID == club_id) \
                        .group_by(User.USER_ID)
        
        total_record  = len(members_query.all())
        
        if month and year:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            members_query = members_query.filter(User_Club.c.JOIN_DATE >= start_date,
                                                User_Club.c.JOIN_DATE < end_date)
            total_record  = len(members_query.all())
            
        # Xem chi tiết câu lạc bộ theo tìm kiếm tên thành viên:    
        if (search_name != 'undefined' and search_name !='') and search_name is not None:
            members_query = members_query.filter(User.FULL_NAME.ilike(f"%{search_name}%"))
            total_record  = len(members_query.all())
        
        # Hiển thị danh sách thành viên của câu lạc bộ
        members_query = members_query.order_by(desc("member_distance")) \
                        .limit(per_page).offset((current_page - 1) * per_page)

        members_results = members_query.all()

        ranked_members = []
        rank = 1
        
        for result in members_results:
            user_id, member_distance, member_pace, member_rank = result
            user = db.query(User).filter(User.USER_ID == user_id).first()
            image_path_user = user.AVATAR_PATH.replace("\\", "/")
            member_join_date = db.query(User_Club.c.JOIN_DATE).filter((User_Club.c.CLUB_ID == club_id) & (User_Club.c.USER_ID == user_id)).first()
            
            ranked_members.append(
                Member(member_id=user.USER_ID,
                    member_name=user.FULL_NAME,
                    member_join_date=member_join_date[0].strftime('%d/%m/%y %H:%M:%S'),
                    member_rank=member_rank,
                    member_image=f"{host}/{image_path_user}",
                    member_distance=round(member_distance or 0, 2),                
                    member_pace=format_seconds(int((member_pace if member_pace is not None else 0) * 60)),
                    member_gender=user.GENDER)
            )
            rank += 1
        
        # total_member = db.query(func.count(User_Club.c.USER_ID)).filter(User_Club.c.CLUB_ID == club_id).scalar()
        total_member = total_record
        total_pages = ceil(total_member / per_page)

        return {
            "ranked_members": ranked_members,
            "per_page":per_page,
            "current_page":current_page,
            "total_record":total_member
            # "total_pages":total_pages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị chi tiết câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
def get_detail_member_activities_club(host: str, club_id: int,
                            member_id: int,
                            current_page: int = Query(1, alias='current_page'), 
                            per_page: int = Query(10, alias='per_page'),
                            from_date: Optional[datetime] = None,
                            to_date: Optional[datetime] = None,
                            activity_name: Optional[str] = None,
                            db: Session = Depends(get_db),
                            user_id: Optional[int]=None):
    club = db.query(Club).filter(Club.CLUB_ID == club_id).one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    user_status = ""
    if user_id is not None:
        user_status = is_user_or_admin(user_id, club_id, db)

    member_detail = db.query(User_Club).join(User, User.USER_ID == User_Club.c.USER_ID) \
                                           .filter(User_Club.c.USER_ID == member_id).first()
    if member_detail is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên này trong câu lạc bộ")
    try:
        activities_member = db.query(User_Club_Activity).filter(User_Club_Activity.CLUB_ID == club_id, User_Club_Activity.USER_ID == member_id)
        total_record = len(activities_member.all())
        if from_date and to_date:
            activities_member = activities_member \
                                .filter(User_Club_Activity.CREATED_AT >= from_date, User_Club_Activity.CREATED_AT <= to_date)
            total_record = len(activities_member.all())
            
        if (activity_name != 'undefined' and activity_name != '') and activity_name is not None:
            activities_member = activities_member \
                                .filter(User_Club_Activity.NAME.ilike(f"%{activity_name}%"))
            total_record = len(activities_member.all())
        
        activities_member = activities_member.order_by(desc(User_Club_Activity.CREATED_AT)) \
                                                .limit(per_page).offset((current_page - 1) * per_page).all()
        
        run_ids = [activate.RUN_ID for activate in activities_member]
        strava_info = db.query(Run.RUN_ID, 
                            Run.STRAVA_RUN_ID).filter(Run.RUN_ID.in_(run_ids)).all()
        strava_run_id = {run_id: strava_run_id for run_id, strava_run_id in strava_info}
        map_info = db.query(Run.RUN_ID, 
                            Run.SUMMARY_POLYLINE).filter(Run.RUN_ID.in_(run_ids)).all()
        map = {run_id: summarry_polyline for run_id, summarry_polyline in map_info}
        type_info = db.query(Run.RUN_ID, 
                            Run.TYPE).filter(Run.RUN_ID.in_(run_ids)).all()
        type = {run_id: type for run_id, type in type_info}
        calo_info = db.query(Run.RUN_ID, 
                            Run.CALORI).filter(Run.RUN_ID.in_(run_ids)).all()
        calo = {run_id: calori for run_id, calori in calo_info}
        heart_beat_info = db.query(Run.RUN_ID, 
                            Run.HEART_RATE).filter(Run.RUN_ID.in_(run_ids)).all()
        heart_beat = {run_id: heart_rate for run_id, heart_rate in heart_beat_info}
        step_info = db.query(Run.RUN_ID, 
                            Run.STEP_RATE).filter(Run.RUN_ID.in_(run_ids)).all()
        step = {run_id: step_rate for run_id, step_rate in step_info}
        durations_info = db.query(Run.RUN_ID, 
                            Run.DURATION).filter(Run.RUN_ID.in_(run_ids)).all()
        duration = {run_id: duration for run_id, duration in durations_info}
        run_reason_ids = db.query(Run.RUN_ID,Flaudulent_Activity_Club.REASON,Flaudulent_Activity_Club.ACTIVITY_ID).outerjoin(Flaudulent_Activity_Club, Flaudulent_Activity_Club.ACTIVITY_ID==Run.STRAVA_RUN_ID) \
                                            .filter(Run.RUN_ID.in_(run_ids)).all()
        
        run_reason_dict = {run_id: run_reason for run_id, run_reason, t in run_reason_ids}
        new_activates = [ActivateMember(activity_id=activate.RUN_ID,
                                    activity_start_date=activate.CREATED_AT.strftime('%d/%m/%Y %H:%M:%S'),
                                    activity_distance=round(activate.DISTANCE or 0, 2), 
                                    activity_pace = format_seconds(int(activate.PACE * 60)) if activate.PACE else "00:00:00",
                                    activity_finish= duration[activate.RUN_ID],
                                    activity_name=activate.NAME,
                                    activity_type=type[activate.RUN_ID],
                                    calo = calo[activate.RUN_ID],
                                    heart_beat = heart_beat[activate.RUN_ID],
                                    step = step[activate.RUN_ID],
                                    activity_link_strava=strava_run_id[activate.RUN_ID],
                                    activity_map=map[activate.RUN_ID],
                                    activity_reason=run_reason_dict[activate.RUN_ID],
                                    activity_status=activate.STATUS) for activate in activities_member]

        

        total_activities = total_record

        total_pages=ceil(total_activities / per_page)

        return {
            "is_admin": user_status == "admin", 
            "detail":new_activates,
            "per_page":per_page,
            "current_page":current_page,
            "total_record":total_activities
            # "total_pages":total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết hoạt động thành viên câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")



