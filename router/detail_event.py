# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User,Event,UserEvent,Organization, User_Event_Activity,  Run, Flaudulent_Activity_Event
from auth.oauth2 import get_current_user
from math import ceil
from sqlalchemy import desc, asc, func, or_
from utils.base_url import get_base_url
from typing import Optional
from utils.format import format_seconds
from datetime import date, datetime, timedelta
from schemas import NewActivate, ActivateMember

router = APIRouter()
def is_admin(user_id: int, event_id: int, db: Session) -> bool:
    admin_club = db.query(Event.ADMIN).filter(Event.EVENT_ID == event_id).scalar()
    
    if user_id == admin_club:
        return True
    else:
        return False
    
def is_user(user_id: int, event_id: int, db: Session) -> bool:
    user_in_club = db.query(UserEvent).filter(
        UserEvent.USER_ID == user_id,
        UserEvent.EVENT_ID == event_id
    ).one_or_none()
    
    if user_in_club:
        return True
    else:
        return False
    
def is_user_or_admin(user_id: int, event_id: int, db: Session) -> str:
    admin_event = db.query(Event.ADMIN).filter(Event.EVENT_ID == event_id).scalar()
    
    if user_id == admin_event:
        return "admin"
    
    user_in_event = db.query(UserEvent).filter(
        UserEvent.USER_ID == user_id,
        UserEvent.EVENT_ID == event_id
    ).one_or_none()
    
    if user_in_event:
        return "member"
    else:
        return "non_member"

# API Lấy chi tiết event trước khi đăng nhập - tung.nguyenson11 -- 21/09/2023
@router.get("/event/{event_id}")
def get_event_details(event_id: int,
                      per_page: int, 
                      current_page: int ,
                      search_name: Optional[str] = None,
                      db: Session = Depends(get_db),
                      host: str = Depends(get_base_url)):
    # Get event details from the database
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try:

        member_list = get_member_list(host, event_id, per_page, current_page, db, search_name)
        total_member_in_event = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event_id).scalar()

        image_path = event.PICTURE_PATH.replace("\\", "/")
        # Create the response JSON
        response_data = {
            "event_id": event_id,
            "event_name": event.TITLE,
            "event_image": f"{host}/{image_path}",
            "eventstartdate": event.START_DATE.strftime("%d/%m/%Y"),
            "eventenddate": event.END_DATE.strftime("%d/%m/%Y"),
            "status": event.STATUS,
            "category": event.RUNNING_CATEGORY,
            "paticipants": total_member_in_event,
            "participants_running": event.NUM_OF_RUNNER,
            "distance_result": round(event.TOTAL_DISTANCE, 2) if event.TOTAL_DISTANCE is not None else 0,
            "content": event.CONTENT,
            "user_status":"",
            "admin_status":"",
            "admin_id":event.ADMIN,
            "min_pace": event.MIN_PACE,
            "max_pace": event.MAX_PACE,
            "table": {
                "per_page_member": per_page,
                "total_record_member": total_member_in_event,
                "current_page_member": current_page,
                "total_page_member": ceil(total_member_in_event / per_page),
                "member": member_list
            }
        }

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị chi tiết giải chạy. Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# API Lấy chi tiết event sao khi đăng nhập - tung.nguyenson11 -- 21/09/2023
@router.get("/event/login/{event_id}")
def get_event_details(event_id: int, 
                      per_page: int, 
                      current_page: int,
                      search_name: Optional[str] = None,  
                      db: Session = Depends(get_db), 
                      current_user:User=Depends(get_current_user),
                      host: str = Depends(get_base_url)):
    # Get event details from the database
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try:
        if current_user is not None:
            user_status = is_user_or_admin(current_user.USER_ID, event_id, db)
        
        member_list = get_member_list(host, event_id, per_page, current_page, db, search_name)
        total_member_in_event = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event_id).scalar()

        image_path = event.PICTURE_PATH.replace("\\", "/")
        # Create the response JSON
        response_data = {
            "event_id": event_id,
            "event_name": event.TITLE,
            "event_image": f"{host}/{image_path}",
            "eventstartdate": event.START_DATE.strftime("%d/%m/%Y"),
            "eventenddate": event.END_DATE.strftime("%d/%m/%Y"),
            "status": event.STATUS,
            "category": event.RUNNING_CATEGORY,
            "paticipants": total_member_in_event,
            "participants_running": event.NUM_OF_RUNNER,
            "distance_result": round(event.TOTAL_DISTANCE, 2) if event.TOTAL_DISTANCE is not None else 0,
            "content": event.CONTENT,
            "user_status":user_status,
            "admin_status": user_status == "admin",
            "admin_id":event.ADMIN,
            "min_pace": event.MIN_PACE,
            "max_pace": event.MAX_PACE,
            "table": {
                "per_page_member": per_page,
                "total_record_member": total_member_in_event,
                "current_page_member": current_page,
                "total_page_member": ceil(total_member_in_event / per_page),
                "member": member_list
            }
        }

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị chi tiết giải chạy sau khi đăng nhập. Vui lòng liên hệ quản trị hệ thống hỗ trợ!") 

# API Lấy chi tiết event trước khi đăng nhập - tung.nguyenson11 -- 23/10/2023
@router.get("/event/overview_public/{event_id}")
def get_event_login(event_id: int,
                      db: Session = Depends(get_db),
                      host: str = Depends(get_base_url)):
    
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
    try:
        total_member_in_event = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event_id).scalar()
        admin_user = db.query(User).filter(User.USER_ID == event.ADMIN).first()
        image_path = event.PICTURE_PATH.replace("\\", "/")
        response_data = {
            "event_id": event_id,
            "event_name": event.TITLE,
            "event_image": f"{host}/{image_path}",
            "eventstartdate": event.START_DATE.strftime("%d/%m/%Y"),
            "eventenddate": event.END_DATE.strftime("%d/%m/%Y"),
            "status": event.STATUS,
            "category": event.RUNNING_CATEGORY,
            "paticipants": total_member_in_event,
            "participants_running": event.NUM_OF_RUNNER,
            "distance_result": round(event.TOTAL_DISTANCE, 2) if event.TOTAL_DISTANCE is not None else 0,
            "content": event.CONTENT,
            "user_status":"",
            "admin_status":"",
            "admin_id":event.ADMIN,
            "min_pace": event.MIN_PACE,
            "max_pace": event.MAX_PACE,
            "admin_name": admin_user.FULL_NAME if admin_user else None
        }

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi chi tiết giải chạy sau khi đăng nhập. Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# API Lấy chi tiết event sao khi đăng nhập - tung.nguyenson11 -- 23/10/2023
@router.get("/event/overview/{event_id}")
def get_event_public(event_id: int, 
                      db: Session = Depends(get_db), 
                      current_user:User=Depends(get_current_user),
                      host: str = Depends(get_base_url)):
    # Get event details from the database
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try: 
        if current_user is not None:
            user_status = is_user_or_admin(current_user.USER_ID, event_id, db)
        
        admin_user = db.query(User).filter(User.USER_ID == event.ADMIN).first()
        
        total_member_in_event = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event_id).scalar()
        image_path = event.PICTURE_PATH.replace("\\", "/")
        # Create the response JSON
        response_data = {
            "event_id": event_id,
            "event_name": event.TITLE,
            "event_image": f"{host}/{image_path}",
            "eventstartdate": event.START_DATE.strftime("%d/%m/%Y"),
            "eventenddate": event.END_DATE.strftime("%d/%m/%Y"),
            "status": event.STATUS,
            "category": event.RUNNING_CATEGORY,
            "paticipants": total_member_in_event,
            "participants_running": event.NUM_OF_RUNNER,
            "distance_result": round(event.TOTAL_DISTANCE, 2) if event.TOTAL_DISTANCE is not None else 0,
            "content": event.CONTENT,
            "user_status":user_status,
            "admin_status": user_status == "admin",
            "admin_id":event.ADMIN,
            "min_pace": event.MIN_PACE,
            "max_pace": event.MAX_PACE,
            "admin_name": admin_user.FULL_NAME if admin_user else None
        }

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị chi tiết giải chạy. Vui lòng liên hệ quản trị hệ thống hỗ trợ!") 

# API hiển thị danh sách hoạt động của giải chạy tung.nguyenson11 -- 23/10/2023
@router.get('/event/new-activity/{event_id}')
def get_event_activity(event_id: int, 
                        hour: Optional[int] = 48, 
                        search_name: Optional[str] = None, 
                        current_page: int = Query(1, alias='current_page'), 
                        per_page: int = Query(10, alias='per_page'), 
                        db: Session = Depends(get_db), 
                        host: str = Depends(get_base_url)):
    return get_new_activities_event( host, 
                                     event_id, 
                                     hour, 
                                     search_name, 
                                     current_page,
                                     per_page,
                                     db)

# API Lấy danh sách các thành viên của event - tung.nguyenson11 -- 23/10/2023
@router.get("/event/rank-member/{event_id}")
def get_event_member(event_id: int, 
                      per_page: int, 
                      current_page: int,
                      search_name: Optional[str] = None,  
                      db: Session = Depends(get_db), 
                      host: str = Depends(get_base_url)):
    # Get event details from the database
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    member_list = get_member_list_1(host, event_id, per_page, current_page, db, search_name)

    return member_list 

# API hiển thị thông tin chi tiết thành viên trong giải chạy tung.nguyenson11 -- 23/10/2023
@router.get('/event/member/overview')
def get_detail_member_event(event_id: int,
                          member_id: int, 
                          db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return get_detail_member_events(host=host, event_id=event_id, member_id=member_id, db=db, user_id=None)

# API hiển thị thông tin chi tiết thành viên trong giải chạy tung.nguyenson11 -- 23/10/2023
@router.get('/event/member/overview_login')
def get_detail_member_event(event_id: int,
                          member_id: int, 
                          db: Session = Depends(get_db), host: str = Depends(get_base_url),
                          current_user:User=Depends(get_current_user)):
    return get_detail_member_events(host=host, event_id=event_id, member_id=member_id, db=db, user_id=current_user.USER_ID)

# API hiển thị danh sách chi tiết hoạt động thành viên trong giải chạy tung.nguyenson11 -- 23/10/2023
@router.get('/event/member/activities')
def  get_member_activitites_event(event_id: int,
                          member_id: int,
                          current_page: int = Query(1, alias='current_page'), 
                          per_page: int = Query(10, alias='per_page'),
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          activity_name: Optional[str] = None,
                          db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return get_detail_member_activities_event(host=host, 
                                                    event_id=event_id, 
                                                    member_id=member_id,
                                                    current_page=current_page,
                                                    per_page=per_page,
                                                    from_date=from_date,
                                                    to_date=to_date,
                                                    activity_name=activity_name,
                                                    db=db, 
                                                    user_id=None)

# API hiển thị danh sách chi tiết hoạt động thành viên trong giải chạy tung.nguyenson11 -- 23/10/2023
@router.get('/event/member/activities_login')
def  get_member_activitites_event(event_id: int,
                          member_id: int,
                          current_page: int = Query(1, alias='current_page'), 
                          per_page: int = Query(10, alias='per_page'),
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          activity_name: Optional[str] = None,
                          db: Session = Depends(get_db), host: str = Depends(get_base_url),
                          current_user:User=Depends(get_current_user)):
    return get_detail_member_activities_event(host=host, 
                                                    event_id=event_id, 
                                                    member_id=member_id,
                                                    current_page=current_page,
                                                    per_page=per_page,
                                                    from_date=from_date,
                                                    to_date=to_date,
                                                    activity_name=activity_name,
                                                    db=db, 
                                                    user_id=current_user.USER_ID)

# hàm lấy danh sách thành viên
def get_member_list(host: str, 
                    event_id: int, 
                    per_page: int, 
                    current_page: int,                    
                    db: Session,
                    search_name: Optional[str] = None):
        offset = (current_page - 1) * per_page
        if (search_name != 'undefined' and search_name != '') and search_name is not None:
            member_list = db.query(UserEvent, User).\
                    join(User, UserEvent.USER_ID == User.USER_ID).\
                    join(Event,UserEvent.EVENT_ID==Event.EVENT_ID).\
                    outerjoin(Organization,User.ORG_ID==Organization.ORG_ID).\
                    filter(UserEvent.EVENT_ID == event_id).\
                    filter(User.FULL_NAME.ilike(f"%{search_name}%"))
        else:                
            member_list = db.query(UserEvent, User).\
                            join(User, UserEvent.USER_ID == User.USER_ID).\
                            join(Event,UserEvent.EVENT_ID==Event.EVENT_ID).\
                            outerjoin(Organization,User.ORG_ID==Organization.ORG_ID).\
                            filter(UserEvent.EVENT_ID == event_id)

        
        member_list = member_list.with_entities(
                            UserEvent.USER_ID,
                            User.FULL_NAME.label("member_name"),
                            UserEvent.RANKING.label("member_rank"),
                            UserEvent.JOIN_DATE.label("member_join_date"),
                            User.AVATAR_PATH.label("member_image"),
                            UserEvent.TOTAL_DISTANCE.label("member_distance"),
                            UserEvent.PACE.label("member_pace"),
                            User.GENDER.label("member_gender"),
                            Organization.ORG_NAME.label("org")
                        ).\
                        order_by(desc(UserEvent.TOTAL_DISTANCE), asc(UserEvent.PACE)).\
                        offset(offset).limit(per_page).all()

        member_data_list = []
        for member_event in member_list:
            
            image_path =  member_event.member_image.replace("\\", "/")
            member_data = {
                "member_id": member_event.USER_ID,
                "member_name": member_event.member_name,
                "member_join_date": member_event.member_join_date.strftime('%d/%m/%Y %H:%M:%S'),
                "member_rank": member_event.member_rank,
                "member_image": f"{host}/{image_path}",
                "member_distance":  round(member_event.member_distance, 2) if member_event.member_distance is not None else 0,
                "member_pace": format_seconds(int((member_event.member_pace if member_event.member_pace is not None else 0) * 60)),
                "member_gender": member_event.member_gender,
                "org": member_event.org
            }
            member_data_list.append(member_data)

        return member_data_list

# hàm lấy danh sách thành viên - tung.nguyenson11 -- 23/10/2023
def get_member_list_1(host: str, 
                    event_id: int, 
                    per_page: int, 
                    current_page: int,                    
                    db: Session,
                    search_name: Optional[str] = None):
    try:
        total_record = None
        offset = (current_page - 1) * per_page
        if (search_name != 'undefined' and search_name != '') and search_name is not None:
            member_list = db.query(UserEvent, User).\
                    join(User, UserEvent.USER_ID == User.USER_ID).\
                    join(Event,UserEvent.EVENT_ID==Event.EVENT_ID).\
                    outerjoin(Organization,User.ORG_ID==Organization.ORG_ID).\
                    filter(UserEvent.EVENT_ID == event_id).\
                    filter(User.FULL_NAME.ilike(f"%{search_name}%"))
            total_record  = len(member_list.all())
        else:                
            member_list = db.query(UserEvent, User).\
                            join(User, UserEvent.USER_ID == User.USER_ID).\
                            join(Event,UserEvent.EVENT_ID==Event.EVENT_ID).\
                            outerjoin(Organization,User.ORG_ID==Organization.ORG_ID).\
                            filter(UserEvent.EVENT_ID == event_id)
            total_record  = len(member_list.all())
        
        member_list = member_list.with_entities(
                            UserEvent.USER_ID,
                            User.FULL_NAME.label("member_name"),
                            UserEvent.RANKING.label("member_rank"),
                            UserEvent.JOIN_DATE.label("member_join_date"),
                            User.AVATAR_PATH.label("member_image"),
                            UserEvent.TOTAL_DISTANCE.label("member_distance"),
                            UserEvent.PACE.label("member_pace"),
                            User.GENDER.label("member_gender"),
                            Organization.ORG_NAME.label("org")
                        ).\
                        order_by(desc(UserEvent.TOTAL_DISTANCE), asc(UserEvent.PACE)).\
                        offset(offset).limit(per_page).all()

        member_data_list = []
        for member_event in member_list:
            
            image_path =  member_event.member_image.replace("\\", "/")
            member_data = {
                "member_id": member_event.USER_ID,
                "member_name": member_event.member_name,
                "member_join_date": member_event.member_join_date.strftime('%d/%m/%Y %H:%M:%S'),
                "member_rank": member_event.member_rank,
                "member_image": f"{host}/{image_path}",
                "member_distance":  round(member_event.member_distance, 2) if member_event.member_distance is not None else 0,
                "member_pace": format_seconds(int((member_event.member_pace if member_event.member_pace is not None else 0) * 60)),
                "member_gender": member_event.member_gender,
                "org": member_event.org
            }
            member_data_list.append(member_data)

        return { "per_page": per_page,
                 "current_page": current_page,
                 "total_record": total_record,
                 "detail": member_data_list
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị anh sách thành viên giải chạy. Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# Hàm hiển thị tất cả hoạt động chạy trong giải chạy tung.nguyenson11 -- 23/10/2023
def get_new_activities_event(host: str, 
                             event_id: int, 
                             hour: Optional[int] = 48,
                             search_name: Optional[str] = None,
                             current_page: int = Query(1, alias='current_page'),
                             per_page: int = Query(10, alias='per_page'),
                             db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Giải chạy không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try:
        start_time = datetime.now() - timedelta(hours=hour)
        latest_activates = db.query(User_Event_Activity).join(User, User_Event_Activity.USER_ID == User.USER_ID) \
                .filter(User_Event_Activity.USER_ID == UserEvent.USER_ID) \
                .filter(UserEvent.EVENT_ID == event_id) \
                .filter(User_Event_Activity.STATUS == "1") \
                .filter(User_Event_Activity.CREATED_AT >= start_time)  

        total_record  = len(latest_activates.all())
        
        # Hiển thị danh sách các hoạt động theo tìm kiếm tên thành viên trong câu lạc bộ
        if (search_name != 'undefined' and search_name !='') and search_name is not None:
            latest_activates = latest_activates \
                                .filter(or_(
                                            User_Event_Activity.NAME.ilike(f"%{search_name}%"),
                                            User.FULL_NAME.ilike(f"%{search_name}%")
                                        ))
            total_record  = len(latest_activates.all())

        latest_activates = latest_activates.order_by(desc(User_Event_Activity.CREATED_AT)) \
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị danh sách hoạt động trong giải chạy đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#hàm lấy ra chi tiết thông tin thành viên trong event tung.nguyenson11 -- 23/10/2023 
def get_detail_member_events(host: str, 
                            event_id: int,
                            member_id: int,
                            db: Session = Depends(get_db),
                            user_id: Optional[int] = None):
    event = db.query(Event).filter(Event.EVENT_ID == event_id).one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải chạy. Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
    user_status = ""
    if user_id is not None:
        user_status = is_user_or_admin(user_id, event_id, db)

    member_detail = db.query(UserEvent).filter(UserEvent.EVENT_ID == event_id, UserEvent.USER_ID == member_id).first()
    total_run = db.query(func.count(User_Event_Activity.RUN_ID)) \
                  .filter(User_Event_Activity.USER_ID == member_id, User_Event_Activity.EVENT_ID == event_id) \
                  .group_by(User_Event_Activity.USER_ID == member_id, User_Event_Activity.EVENT_ID == event_id).scalar()
    if member_detail is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên này trong câu lạc bộ")
    try:
        user = db.query(User).filter(User.USER_ID == member_detail.USER_ID).first()

        image_path = user.AVATAR_PATH.replace("\\", "/")
        myevent={       
                "user_id": member_id,
                "fullname": user.FULL_NAME,
                "image" : f"{host}/{image_path}",
                "total_distance" : round(member_detail.TOTAL_DISTANCE,2) if member_detail.TOTAL_DISTANCE else 0,
                "avg_pace" : format_seconds(int(member_detail.PACE * 60)) if member_detail.PACE else "00:00:00",
                "total_run" : total_run,
                "strava_user_link": user.STRAVA_ID,
                "is_admin": user_status == "admin",
        }

        return myevent
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết thành viên câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
def get_detail_member_activities_event( host: str, event_id: int,
                                        member_id: int,
                                        current_page: int = Query(1, alias='current_page'), 
                                        per_page: int = Query(10, alias='per_page'),
                                        from_date: Optional[datetime] = None,
                                        to_date: Optional[datetime] = None,
                                        activity_name: Optional[str] = None,
                                        db: Session = Depends(get_db),
                                        user_id: Optional[int]=None):
    event = db.query(Event).filter(Event.EVENT_ID == event_id).one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    user_status = ""
    if user_id is not None:
        user_status = is_user_or_admin(user_id, event_id, db)
    member_detail = db.query(UserEvent).join(User, User.USER_ID == UserEvent.USER_ID) \
                                           .filter(UserEvent.USER_ID == member_id).first()
    if member_detail is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên này trong câu lạc bộ")
    try:
        activities_member = db.query(User_Event_Activity).filter(User_Event_Activity.EVENT_ID == event_id, User_Event_Activity.USER_ID == member_id)
        total_record = len(activities_member.all())
        if from_date and to_date:
            activities_member = activities_member \
                                .filter(User_Event_Activity.CREATED_AT >= from_date, User_Event_Activity.CREATED_AT <= to_date)
            total_record = len(activities_member.all())
            
        if (activity_name != 'undefined' and activity_name != '') and activity_name is not None:
            activities_member = activities_member \
                                .filter(User_Event_Activity.NAME.ilike(f"%{activity_name}%"))
            total_record = len(activities_member.all())
        
        activities_member = activities_member.order_by(desc(User_Event_Activity.CREATED_AT)) \
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
        run_reason_ids = db.query(Run.RUN_ID,Flaudulent_Activity_Event.REASON,Flaudulent_Activity_Event.ACTIVITY_ID).outerjoin(Flaudulent_Activity_Event, Flaudulent_Activity_Event.ACTIVITY_ID==Run.STRAVA_RUN_ID) \
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
            "is_admin": user_status =="admin" ,
            "detail":new_activates,
            "per_page":per_page,
            "current_page":current_page,
            "total_record":total_activities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hiển thị thông tin chi tiết hoạt động thành viên câu lạc bộ đang lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")