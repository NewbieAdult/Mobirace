# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import HTTPException, Form, UploadFile
from sqlalchemy.orm.session import Session
from db.models import Event, User,UserEvent,User_Role, User_Event_Activity, Flaudulent_Activity_Event
from sqlalchemy import case, update, func, and_
from schemas import Homepage, DataModel, EventBase, FraudulentActivity, Change_admin_event
from math import ceil
from datetime import datetime,timezone
from typing import Union
from jobs.tasks import *
import os, shutil
import pytz

#get homepage
def get_homepage(host: str, db: Session):
    try:
        events = db.query(Event).filter(Event.OUTSTANDING == '1').all()
        homepage_data = []
        for event in events:
            image_path = event.PICTURE_PATH.replace("\\", "/")
            homepage = Homepage(
                EVENT_ID=event.EVENT_ID,
                TITLE=event.TITLE,
                PICTURE_PATH=f"{host}/{image_path}"
            )
            homepage_data.append(homepage)
        return homepage_data
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị các giải chạy lên trang chủ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

#get event
def get_events_info(host: str, db: Session, status: int, current_page: int = 1, per_page: int = 10) -> EventBase:
    try:
        current_datetime = datetime.now()
        update_query = (
                            update(Event)
                            .values(
                                STATUS =case(
                                    (Event.START_DATE > current_datetime, 3),  # Chưa diễn ra
                                    (Event.END_DATE < current_datetime, 2),    # Đã kết thúc
                                    else_=1  # Đang diễn ra (mặc định)
                                )
                            )
                        )

        db.execute(update_query)
        db.commit()
        skip = (current_page - 1) * per_page

        if status == 1:  # Đang diễn ra
            filter_clause = and_(Event.START_DATE <= datetime.now(), Event.END_DATE >= datetime.now())
        elif status == 2:  # Đã kết thúc
            filter_clause = Event.END_DATE < datetime.now()
        elif status == 3:  # Chưa diễn ra
            filter_clause = Event.START_DATE > datetime.now()
        else:
            filter_clause = True  # Hiển thị tất cả sự kiện
        total_events = db.query(func.count(Event.EVENT_ID)).filter(filter_clause).scalar()
        events = db.query(Event).filter(filter_clause).offset(skip).limit(per_page).all()
        data = []
        
        for event in events:
            participants_count = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event.EVENT_ID).scalar()
            participants_running_count = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event.EVENT_ID, UserEvent.TOTAL_DISTANCE > 0).scalar()
            if event.STATUS == status or status==0:
                if status == 1:
                    status_name = "Đang diễn ra"
                elif status == 2:
                    status_name = "Đã kết thúc"
                else:
                    status_name = "Sắp diễn ra" 
                image_path = event.PICTURE_PATH.replace("\\", "/")
                data_model = DataModel(
                    eventid=event.EVENT_ID,
                    image= f"{host}/{image_path}",
                    eventname=event.TITLE,
                    eventstartdate=event.START_DATE.strftime('%Y-%m-%d %H:%M:%S'),
                    eventenddate=event.END_DATE.strftime('%Y-%m-%d %H:%M:%S'),
                    category=event.RUNNING_CATEGORY,
                    paticipants=participants_count,
                    participants_running=participants_running_count,
                    event_status=status_name,
                    oustanding=event.OUTSTANDING
                )
                data.append(data_model)

        total_page = ceil(total_events / per_page)
        event_base = EventBase(
            per_page=per_page,
            total_event=total_events,
            current_page=current_page,
            total_page=total_page,
            data=data,
        )

        db.commit()
        
        return event_base
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị danh sách giải chạy! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def get_event_by_eventname(host: str, eventname :str, status:int, per_page : int, current_page : int, db: Session):
    try:
        skip = (current_page - 1) * per_page
        events = db.query(Event).filter(and_(Event.TITLE.like(f"%{eventname}%"), Event.STATUS == status))
        total_events = len(events.all())
        events = events.offset(skip).limit(per_page).all()
        data = []
        for event in events:
            participants_count = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event.EVENT_ID).scalar()
            participants_running_count = db.query(func.count(UserEvent.USER_ID)).filter(UserEvent.EVENT_ID == event.EVENT_ID, UserEvent.TOTAL_DISTANCE > 0).scalar()
            image_path = event.PICTURE_PATH.replace("\\", "/")
            if status == 1:
                status_name = "Đang diễn ra"
            elif status == 2:
                status_name = "Đã kết thúc"
            else:
                status_name = "Sắp diễn ra"    

            data_model = DataModel(
                eventid=event.EVENT_ID,
                image=f"{host}/{image_path}",
                eventname=event.TITLE,
                eventstartdate=event.START_DATE.strftime('%Y-%m-%d %H:%M:%S'),
                eventenddate=event.END_DATE.strftime('%Y-%m-%d %H:%M:%S'),
                category=event.RUNNING_CATEGORY,
                paticipants=participants_count,
                participants_running=participants_running_count,
                event_status=status_name,
                oustanding=event.OUTSTANDING
            )
            data.append(data_model)
        total_page = ceil(total_events / per_page)
        event_base = EventBase(
            per_page=per_page,
            total_event=total_events,
            current_page=current_page,
            total_page=total_page,
            data=data,
        )
        return event_base
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi tìm kiếm giải chạy! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def create_event(   db: Session, 
                    current_user: User,
                    title: str = Form(...),
                    image: Union[UploadFile,str] = Form(None),
                    start_day: datetime = Form(...),
                    end_day: datetime = Form(...),
                    category: str = Form(None),
                    content: str = Form(None),
                    max_pace: float = Form(None),
                    min_pace: float = Form(None)):

    existing_event = db.query(Event).filter(Event.TITLE == title).first()
    if existing_event:
        raise HTTPException(status_code=400, detail="Giải chạy đã tồn tại")
    
    if image == 'null' or image is None:
        raise HTTPException(status_code=422, detail="Vui lòng chọn hình ảnh giải chạy!")
    try:
        start_day = start_day.replace(tzinfo=timezone.utc)
        end_day = end_day.replace(tzinfo=timezone.utc)
        current_datetime = datetime.now(timezone.utc)

        if start_day > current_datetime:
            status = 3  # Chưa diễn ra
        elif end_day < current_datetime:
            status = 2  # Đã kết thúc
        else:
            status = 1  # Đang diễn ra
        formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename= f"event_add_{formatted_date}.jpg"

        with open(os.path.join("images", filename), "wb") as f:
            shutil.copyfileobj(image.file, f) 

        image_path = os.path.join('images', filename)
        created_at = datetime.now(timezone.utc)
        add_event = Event(
            TITLE=title,
            PICTURE_PATH=image_path,
            START_DATE=start_day,
            END_DATE=end_day,
            RUNNING_CATEGORY=category,
            CONTENT=content,
            CREATE_AT=created_at,
            USER_CREATE=current_user.USER_ID,
            MAX_PACE=max_pace,
            MIN_PACE=min_pace,
            STATUS=status,
            ADMIN=current_user.USER_ID
        )
        db.add(add_event)
        db.commit()
        db.refresh(add_event)
        update_ranking_user_event(db)
        update_ranking_event(db)
        return {"status": 200, "detail": "Tạo giải chạy thành công"}
    except Exception:
        raise HTTPException(status_code=500, detail="Tạo giải chạy không thành công! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
   
#user vào event
def join_event(event_id: int, current_user: User, db: Session):
    existing_user_event = db.query(UserEvent).filter(UserEvent.USER_ID == current_user.USER_ID, UserEvent.EVENT_ID == event_id).first()
    if existing_user_event:
        raise HTTPException(status_code=200, detail="Bạn đã tham gia giải chạy này")
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải chạy")
    try:
        new_user_event = UserEvent(
            USER_ID=current_user.USER_ID,
            EVENT_ID=event_id,
            JOIN_DATE=datetime.now(),
            TOTAL_DISTANCE=UserEvent.TOTAL_DISTANCE
        )
        db.add(new_user_event)
        db.commit()
        sync_runs_to_user_event_activity_by_id(db, current_user.USER_ID)
        update_ranking_user_event(db)
        update_ranking_event(db)
        
        return {"status": 200, "detail": "Đăng ký vào giải chạy thành công"}
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi thao tác tham gia giải chạy! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# user thoát event
def leave_event(event_id: int, current_user: User, db: Session):
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải chạy có ID {}".format(event_id))
    
    existing_user_event = db.query(UserEvent).filter(UserEvent.USER_ID == current_user.USER_ID, UserEvent.EVENT_ID == event_id).first()
    if not existing_user_event:
        raise HTTPException(status_code=200, detail="Bạn chưa tham gia giải chạy này")
    
    event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    
    try:
        db.query(User_Event_Activity).filter(User_Event_Activity.EVENT_ID == event_id, User_Event_Activity.USER_ID == current_user.USER_ID).delete()    
        db.delete(existing_user_event)
        db.commit()
        update_ranking_user_event(db)
        update_ranking_event(db)
        return {"status": 200, "detail": "Thao tác thành công!"}
    except Exception:
        raise HTTPException(status_code=500, detail="Hủy tham gia giải chạy không thành công! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def update_event(   event_id: int, 
                    db: Session, 
                    title: str = Form(...),
                    image: Union[UploadFile,str] = Form(None),
                    start_day: datetime = Form(...),
                    end_day: datetime = Form(...),
                    category: str = Form(None),
                    status: int = Form(None),
                    content: str = Form(None),
                    max_pace: float = Form(None),
                    min_pace: float = Form(None), ):
    
    existing_event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not existing_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy giải chạy!")
    try:
        if image != 'null':
            start_day = start_day.replace(tzinfo=timezone.utc)
            end_day = end_day.replace(tzinfo=timezone.utc)
            current_datetime = datetime.now(timezone.utc)
            if start_day > current_datetime:
                status= 3  # Chưa diễn ra
            elif end_day < current_datetime:
                status = 2  # Đã kết thúc
            else:
                status = 1  # Đang diễn ra
            formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename= f"event_add_{formatted_date}.jpg"

            with open(os.path.join("images", filename), "wb") as f:
                shutil.copyfileobj(image.file, f)

            image_path = os.path.join('images', filename)
            update_data = {
                "TITLE": title,
                "CONTENT": content,
                "PICTURE_PATH": image_path,
                "START_DATE": start_day.strftime('%Y-%m-%d %H:%M:%S'),
                "END_DATE": end_day.strftime('%Y-%m-%d %H:%M:%S'),
                "RUNNING_CATEGORY": category,
                "MAX_PACE": max_pace,
                "MIN_PACE": min_pace,
                "STATUS": status
            }
            db.query(Event).filter(Event.EVENT_ID == event_id).update(update_data)
            db.commit()
            update_ranking_user_event(db)
            update_ranking_event(db)
        else:
            start_day = start_day.replace(tzinfo=timezone.utc)
            end_day = end_day.replace(tzinfo=timezone.utc)
            current_datetime = datetime.now(timezone.utc)
            if start_day > current_datetime:
                status= 3  # Chưa diễn ra
            elif end_day < current_datetime:
                status = 2  # Đã kết thúc
            else:
                status = 1  # Đang diễn ra
            update_data = {
                "TITLE": title,
                "CONTENT": content,
                "PICTURE_PATH": existing_event.PICTURE_PATH,
                "START_DATE": start_day.strftime('%Y-%m-%d %H:%M:%S'),
                "END_DATE": end_day.strftime('%Y-%m-%d %H:%M:%S'),
                "RUNNING_CATEGORY": category,
                "MAX_PACE": max_pace,
                "MIN_PACE": min_pace,
                "STATUS": status
            }

            db.query(Event).filter(Event.EVENT_ID == event_id).update(update_data)
            db.commit()
            update_ranking_user_event(db)
            update_ranking_event(db)

        return {"status": 200, "detail": "Cập nhật thông tin giải chạy thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cập nhật thông tin giải chạy thất bại")
# delete event thien.tranthi 19/10/2023
def delete_event(event_id: int, db: Session):
    existing_event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
    if not existing_event:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải chạy")
    try:
        old_image_path = existing_event.PICTURE_PATH
        if old_image_path and  os.path.exists(old_image_path):
                old_image_filename = os.path.basename(old_image_path)
                if old_image_filename:
                        os.remove(old_image_path)
        db.query(User_Event_Activity).filter(User_Event_Activity.EVENT_ID == event_id).delete()
        db.query(UserEvent).filter(UserEvent.EVENT_ID == event_id).delete()
        db.delete(existing_event)
        db.commit() 
        update_club_ranking(db)
        return {"status": 200, "detail": "Xóa giải chạy thành công"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Xóa giải chạy không thành công! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
# change admin event thien.tranthi 19/10/2023
def change_admin_event(request:Change_admin_event, db:Session, current_user:User):
    event = db.query(Event).filter(Event.EVENT_ID == request.event_id, Event.ADMIN == current_user.USER_ID).first()
    if not event:
        raise HTTPException(status_code=404, detail="Câu lạc bồ không tồn tại!")
    
    new_admin = db.query(User).filter(User.USER_ID == request.admin_id).one_or_none()
    if not new_admin:
        raise HTTPException(status_code=404, detail="Người dùng mới không tồn tại!")
    try:
        # Cập nhật admin của club
        event.ADMIN = request.admin_id
        db.commit()
        return {"message": "Thay đổi admin thành công", "status_code": 200} 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Đổi admin thất bại! Vui lòng liên hệ  quản trị hệ thống để hỗ trợ!")
       
def get_user_event_activity(user_id: int, event_id: int, db: Session):
    try:
        # Lấy thông tin user_event_activity dựa trên user_id và event_id
        activity = db.query(User_Event_Activity).filter(
            User_Event_Activity.USER_ID == user_id,
            User_Event_Activity.EVENT_ID == event_id,
            # User_Event_Activity.STATUS== 1
        ).all()

        if not activity:
            raise HTTPException(status_code=404, detail="User event activity not found")
        for res in activity:
            res.CREATED_AT = res.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S")
        return activity

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#
def hide_activity_in_event(run_id: int, event_id: int, reason: str, db: Session, current_user: User):
    try:
        # Lấy thông tin user_event_activity dựa trên run_id và event_id
        activity = db.query(User_Event_Activity).filter(
            User_Event_Activity.RUN_ID == run_id,
            User_Event_Activity.EVENT_ID == event_id,
            User_Event_Activity.STATUS == 1
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity in event not found")

        # Kiểm tra xem người dùng có ROLE_ID = 1 hay không
        user_roles = db.query(User_Role).filter(
            User_Role.USER_ID == current_user.USER_ID
        ).all()

        user_role_ids = [user_role.ROLE_ID for user_role in user_roles]

        if 1 in user_role_ids:  # Nếu ROLE_ID = 1 tồn tại trong danh sách ROLE_ID của người dùng
            # Đặt STATUS = 0 để ẩn hoạt động
            activity.STATUS = 0
            activity.REASON = reason
            db.commit()
            update_ranking_user_event(db)
            update_user_club_distance_and_pace(db)
            update_user_club_ranking(db)
            calculate_club_total_distance(db)
            update_club_ranking(db)
            update_user_ranking(db)
            update_ranking_event(db)
            return {"message": "Activity in event hidden successfully"}
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to hide this activity")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

def re_hide_activity_in_event(run_id: int, event_id: int, db: Session, current_user: User):
    try:
        activity = db.query(User_Event_Activity).filter(
            User_Event_Activity.RUN_ID == run_id,
            User_Event_Activity.EVENT_ID == event_id,
            User_Event_Activity.STATUS == 0
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity in event not found")
        user_roles = db.query(User_Role).filter(
            User_Role.USER_ID == current_user.USER_ID
        ).all()

        user_role_ids = [user_role.ROLE_ID for user_role in user_roles]

        if 1 in user_role_ids:  
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
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to hide this activity")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

def set_outstanding(event_id:int, db:Session):
    event=db.query(Event).filter(Event.EVENT_ID==event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.OUTSTANDING!=1:
        event.OUTSTANDING=1
        db.commit()
        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        update_user_ranking(db)
        update_ranking_event(db)
        return {"message": "update thành công"}
    else:
        raise HTTPException(status_code=400, detail="Giải chạy này đã là giải chạy nổi bật")
    
def un_set_outstanding(event_id:int, db:Session):
    event=db.query(Event).filter(Event.EVENT_ID==event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.OUTSTANDING==1:
        event.OUTSTANDING=0
        db.commit()
        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        update_user_ranking(db)
        update_ranking_event(db)
        return {"message": "update thành công"}
    else:
        raise HTTPException(status_code=400, detail="Giải chạy này hiện tại chưa nằm trong danh sách giải chạy nổi bật")
    
def get_user_event_activity_by_date(user_id: int, event_id: int, db: Session, textSearch: str = None):
    try:
        query = db.query(User_Event_Activity).filter(
            User_Event_Activity.USER_ID == user_id,
            User_Event_Activity.EVENT_ID == event_id
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

#can.lt 15/10/23
def deactive_activity(payload: FraudulentActivity, db: Session):
    run = db.query(Run).filter(Run.RUN_ID == payload.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động")
    event = db.query(Event).filter(Event.EVENT_ID == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    if payload.user_id != event.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")
    
    # Kiểm tra xem dữ liệu đã tồn tại hay chưa
    existing_data = db.query(Flaudulent_Activity_Event).filter(
        Flaudulent_Activity_Event.EVENT_ID == payload.event_id,
        Flaudulent_Activity_Event.ACTIVITY_ID == run.STRAVA_RUN_ID
    ).first()
    if existing_data:
        raise HTTPException(status_code=409, detail="Dữ liệu đã tồn tại")

    # Tạo dữ liệu mới
    new_data = Flaudulent_Activity_Event(
        CREATED_ID = payload.user_id,
        EVENT_ID = payload.event_id,
        ACTIVITY_ID = run.STRAVA_RUN_ID,
        REASON = payload.reason,
        CREATE_DATETIME = datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_data)
    db.query(User_Event_Activity).filter(
        User_Event_Activity.EVENT_ID == payload.event_id,
        User_Event_Activity.RUN_ID == payload.run_id
    ).update({"STATUS": 0})
    update_ranking_user_event(db, payload.event_id)
    update_ranking_event(db, payload.event_id)
    db.commit()
    return {"status_code": 200, "detail": "Hủy bỏ dữ liệu chạy thành công"}

#can.lt 14/10/23
def active_activity(payload: FraudulentActivity, db: Session):
    run = db.query(Run).filter(Run.RUN_ID == payload.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động")
    event = db.query(Event).filter(Event.EVENT_ID == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    if payload.user_id != event.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")
    
    # Xóa dữ liệu gian lận
    record = db.query(Flaudulent_Activity_Event).filter(
        Flaudulent_Activity_Event.EVENT_ID == payload.event_id,
        Flaudulent_Activity_Event.ACTIVITY_ID == run.STRAVA_RUN_ID
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu gian lận")
    db.delete(record)
    # active lại dữ liệu chạy
    db.query(User_Event_Activity).filter(
        User_Event_Activity.EVENT_ID == payload.event_id,
        User_Event_Activity.RUN_ID == payload.run_id
    ).update({"STATUS": 1})
    update_ranking_user_event(db, payload.event_id)
    update_ranking_event(db, payload.event_id)
    db.commit()
    return {"status_code": 200, "detail": "Kích hoạt lại dữ liệu chạy thành công"}