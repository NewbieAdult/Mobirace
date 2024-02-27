from db.database import SessionLocal
from db.models import User,Run, User_Role, User_Event_Activity, User_Club_Activity
from utils.strava import get_all_activities,refresh_strava_token, exchange_authorization_code_at, get_activity_info_by_id
from datetime import datetime, timedelta
from sqlalchemy.orm.session import Session
from sqlalchemy import update, delete
from schemas import WebhookResponse
from typing import Optional

from utils.validation import check_pace
from jobs.tasks import *
from utils.format import *

from router import webhook

def sync_activities(authorization_code:str):
    access_token = exchange_authorization_code_at(authorization_code)
    if access_token:
        user_activities = get_all_activities(access_token)
        db = SessionLocal()
        for activity in user_activities:
            name=activity['name']
            strava_run_id=activity['id']
            type=activity['type']
            distance=activity['distance']
            duration=format_seconds(activity['moving_time'])
            calori=activity.get('calories',0)
            start_day_str=activity['start_date_local']
            create_at=datetime.strptime(start_day_str, "%Y-%m-%dT%H:%M:%SZ")
            heart_rate = activity.get('heartrate', 0)
            step_rate = activity.get('step_rate', 0)
            pace=activity['moving_time']/(activity['distance']/1000)/60
            right_pace=check_pace(pace)
            summary_polyline=activity['map']['summary_polyline']
            new_activity = Run(NAME=name,STRAVA_RUN_ID=strava_run_id,
                               TYPE=type,DISTANCE=distance,DURATION=duration,CALORI=calori,
                               CREATED_AT=create_at,HEART_RATE=heart_rate,STEP_RATE=step_rate,
                               SUMMARY_POLYLINE=summary_polyline,PACE=right_pace)
            db.add(new_activity)
        db.commit()
        db.close()
        return {"message": "Activities synced successfully"}
    
def get_run_by_stravarunid(object_id : int, db: Session):
    
    run = db.query(Run).filter(Run.STRAVA_RUN_ID == object_id).first()
    try:
        return run
    except Exception:
        raise HTTPException(status_code=500, detail="Không tồn tại hoạt động này! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def add_all_activities(user_activities, db: Session, current_user: User):
    for activity in user_activities:
        start_date_local = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
        if start_date_local < current_user.CREATED_AT:
            continue
        pace = float(60 / (activity['average_speed'] * 3.6)) if activity['average_speed'] != 0 and activity['average_speed'] is not None else 0
        run = db.query(Run).filter(Run.STRAVA_RUN_ID == activity['id']).first()
        if run is None:
            new_run = Run(
                    USER_ID = current_user.USER_ID,
                    STRAVA_RUN_ID = activity['id'],
                    NAME = activity['name'],
                    DISTANCE = activity['distance']/1000,        
                    DURATION = format_seconds(activity['moving_time']),
                    PACE = pace,
                    CALORI = activity.get('calories',None),
                    CREATED_AT = start_date_local,
                    STATUS=check_pace(pace),
                    TYPE = activity['type'],
                    HEART_RATE=activity.get('average_heartrate', None),
                    STEP_RATE=activity.get('step_rate', None),
                    SUMMARY_POLYLINE =activity['map']['summary_polyline']   
                )
            db.add(new_run)    
    # db.commit()

def update_run_eventwebhook(res :WebhookResponse, db: Session):
    run = get_run_by_stravarunid(res.object_id, db)
    if res.updates.get('title'):
        run.NAME = res.updates['title']
    if res.updates.get('type'):
        run.TYPE = res.updates['type']
    db.commit()

def add_run_eventwebhook(res :WebhookResponse, db: Session):
    user = db.query(User).filter(User.STRAVA_ID == res.owner_id).first()
    activity = get_activity_info_by_id(res.object_id, user.STRAVA_ACCESS_TOKEN)
    if activity == None:
        access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
        activity = get_activity_info_by_id(res.object_id, access_token)
        user.STRAVA_ACCESS_TOKEN = access_token
        user.STRAVA_REFRESH_TOKEN = new_refresh_token
        db.commit()
    if db.query(Run).filter(Run.STRAVA_RUN_ID == res.object_id).first() != None:
        return 200
    pace = float(60 / (activity['average_speed'] * 3.6)) if activity['average_speed'] != 0 and activity['average_speed'] is not None else 0
    start_date_local = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
    if start_date_local < user.CREATED_AT:
        return "Dữ liệu chạy không hợp lệ!"
    new_run = Run(
                USER_ID = user.USER_ID,
                STRAVA_RUN_ID = activity['id'],
                NAME = activity['name'],
                DISTANCE = activity['distance']/1000,        
                DURATION = format_seconds(activity['moving_time']),
                PACE = pace,
                CALORI = activity.get('calories',None),
                CREATED_AT = start_date_local,
                STATUS=check_pace(pace),
                TYPE = activity['type'],
                HEART_RATE=activity.get('average_heartrate', None),
                STEP_RATE=activity.get('step_rate', None),
                SUMMARY_POLYLINE =activity['map']['polyline']   
            )
    db.add(new_run)
    db.commit()
    #cập nhật user
    update_user_ranking_by_id(db, user.USER_ID)
    
    # cập nhật event
    sync_runs_to_user_event_activity_by_id(db, user.USER_ID)
    update_ranking_user_event(db)

    update_ranking_event(db)

    # cập nhật club
    sync_runs_to_user_club_activity(db)
    update_user_club_distance_and_pace(db)
    update_user_club_ranking(db)
    calculate_club_total_distance(db)
    update_club_ranking(db)

    db.commit()
    return 200

def re_initialize_activities(db: Session): 
        webhook.router.RE_INIT_STATUS= True
        
        update_statement = update(User).values(SYNC_STATUS='0')
        db.execute(update_statement)
        db.commit()
 
        user_list = db.query(User).filter(User.STRAVA_ID.isnot(None)).all()
        for user in user_list: 
            try:
                after = int(user.CREATED_AT.timestamp())   
                activity = get_all_activities(user.STRAVA_ACCESS_TOKEN, after)
                if activity is None:
                    access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
                    user.STRAVA_ACCESS_TOKEN = access_token
                    user.STRAVA_REFRESH_TOKEN = new_refresh_token
                db.commit()

                db.query(User_Club_Activity).filter(User_Club_Activity.USER_ID == user.USER_ID, User_Club_Activity.STATUS == '1').delete()
                db.query(User_Event_Activity).filter(User_Event_Activity.USER_ID == user.USER_ID, User_Event_Activity.STATUS == '1').delete() 
                db.commit()   
                sql_query = text("""
                                    DELETE FROM RUN a
                                    WHERE a.STATUS = '1' 
                                    AND a.USER_ID = :user_id
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM USER_CLUB_ACTIVITY b
                                        WHERE b.USER_ID = :user_id AND b.STATUS = '0'
                                        AND b.RUN_ID = a.RUN_ID
                                    )
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM USER_EVENT_ACTIVITY c
                                        WHERE c.USER_ID = :user_id AND c.STATUS = '0'
                                        AND c.RUN_ID = a.RUN_ID
                                    )
                                """)            
                db.execute(sql_query, {"user_id": user.USER_ID})
                db.commit()
                
                add_all_activities(activity, db, user)
                update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='1')
                db.execute(update_statement)
                
                db.commit()
            except:
                db.rollback() 
                update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='-1')
                db.execute(update_statement)
                db.commit()
          
        for data in webhook.temp_data_list:
            if data.aspect_type=='update':
                update_run_eventwebhook(data,db)
            else :
                add_run_eventwebhook(data,db)
            
        webhook.temp_data_list.clear()
        sync_runs_to_user_event_activity(db)
        sync_runs_to_user_club_activity(db)

        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        update_user_ranking(db)
        update_ranking_event(db)
        
        update_statement = update(User).where(User.SYNC_STATUS =='0').values(SYNC_STATUS='-2')
        db.execute(update_statement)
        db.commit()
        webhook.router.RE_INIT_STATUS= False

def re_initialize_activity(user_id:int, db: Session):
    

    user_list = db.query(User).filter(User.STRAVA_ID.isnot(None)).all()
    user = db.query(User).filter(User.STRAVA_ID.isnot(None), User.USER_ID == user_id).first()
    if user not in user_list:
        update_statement = update(User).where(User.USER_ID == user_id).values(SYNC_STATUS='-2')
        db.execute(update_statement)
        db.commit()
        return
 
    update_statement = update(User).where(User.USER_ID == user_id).values(SYNC_STATUS='0')
    db.execute(update_statement)
    db.commit()
    try:
        after = int(user.CREATED_AT.timestamp())
        activity = get_all_activities(user.STRAVA_ACCESS_TOKEN, after)
        if activity is None:
            access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
            activity = get_all_activities(access_token, after)
            user.STRAVA_ACCESS_TOKEN = access_token
            user.STRAVA_REFRESH_TOKEN = new_refresh_token
        db.commit()
    except Exception as e:
        db.rollback() 
        update_statement = update(User).where(User.USER_ID == user_id).values(SYNC_STATUS='-1')
        db.execute(update_statement)
        db.commit()
        raise HTTPException(status_code=500, detail="Lỗi kết nối Strava khi đồng bộ dữ liệu người dùng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try:
        db.query(User_Club_Activity).filter(User_Club_Activity.USER_ID == user.USER_ID, User_Club_Activity.STATUS == '1').delete()
        db.query(User_Event_Activity).filter(User_Event_Activity.USER_ID == user.USER_ID, User_Event_Activity.STATUS == '1').delete() 
        db.commit()   
        sql_query = text("""
                            DELETE FROM RUN a
                            WHERE a.STATUS = '1' 
                            AND a.USER_ID = :user_id
                            AND NOT EXISTS (
                                SELECT 1
                                FROM USER_CLUB_ACTIVITY b
                                WHERE b.USER_ID = :user_id AND b.STATUS = '0'
                                AND b.RUN_ID = a.RUN_ID
                            )
                            AND NOT EXISTS (
                                SELECT 1
                                FROM USER_EVENT_ACTIVITY c
                                WHERE c.USER_ID = :user_id AND c.STATUS = '0'
                                AND c.RUN_ID = a.RUN_ID
                            )
                        """)            
        db.execute(sql_query, {"user_id": user.USER_ID})
        db.commit()
        
        add_all_activities(activity, db, user)
        db.commit()
    except Exception as e:
        db.rollback() 
        update_statement = update(User).where(User.USER_ID == user_id).values(SYNC_STATUS='-1')
        db.execute(update_statement)
        db.commit()
        raise HTTPException(status_code=500, detail="Lỗi đồng bộ dữ liệu người dùng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    #cập nhật user
    update_user_ranking_by_id(db, user.USER_ID)

    # cập nhật event
    sync_runs_to_user_event_activity(db)
    sync_runs_to_user_club_activity(db)

    update_ranking_user_event(db)
    update_user_club_distance_and_pace(db)
    update_user_club_ranking(db)
    calculate_club_total_distance(db)
    update_club_ranking(db)
    update_user_ranking(db)
    update_ranking_event(db)

    update_statement = update(User).where(User.USER_ID == user_id).values(SYNC_STATUS='1')
    db.execute(update_statement)
    db.commit()
   

def hide_activity(run_id: int, db: Session, current_user: User, reason: Optional[str] = None):
    user = db.query(User).join(Run, Run.USER_ID == User.USER_ID).filter(Run.RUN_ID == run_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Người dùng này không tồn tại! Vui lòng liên hệ quản trị để được hỗ trợ!")
    run = db.query(Run).filter(Run.RUN_ID == run_id).first()
    user_event_run = db.query(User_Event_Activity). \
                    join(Run, Run.RUN_ID == User_Event_Activity.RUN_ID). \
                    filter(Run.RUN_ID == run_id).first()
    user_club_run = db.query(User_Club_Activity). \
                    join(Run, Run.RUN_ID == User_Club_Activity.RUN_ID). \
                    filter(Run.RUN_ID == run_id).first()
    try:

        # Kiểm tra xem người dùng hiện tại có phải admin hay ko
        user_roles = db.query(User_Role).filter(
            User_Role.USER_ID == current_user.USER_ID
        ).all()

        user_role_ids = [user_role.ROLE_ID for user_role in user_roles]

        if 1 in user_role_ids:  
            run.STATUS = 0
            run.REASON = reason
            if user_event_run:
                user_event_run.STATUS = 0
            if user_club_run:
                user_club_run.STATUS = 0
            db.commit()
             #cập nhật user
            update_user_ranking_by_id(db, user.USER_ID)
            
            # cập nhật event
            update_ranking_user_event(db)
            update_ranking_event(db)
            # cập nhật club
            update_user_club_distance_and_pace(db)
            update_user_club_ranking(db)
            calculate_club_total_distance(db)
            update_club_ranking(db)

            db.commit()
            return {"message": "Khóa hoạt động thành công!"}
        else:
            raise HTTPException(status_code=403, detail="Lỗi trong quá trình khóa hoạt động! Vui lòng liên hệ quản trị hệ thống để được hỗ trợ!")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

def re_hide_activity(run_id: int, db: Session, current_user: User, reason: Optional[str] = None):
    user = db.query(User).join(Run, Run.USER_ID == User.USER_ID).filter(Run.RUN_ID == run_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Người dùng này không tồn tại! Vui lòng liên hệ quản trị để được hỗ trợ!")
    run = db.query(Run).filter(Run.RUN_ID == run_id).first()
    user_event_run = db.query(User_Event_Activity). \
                    join(Run, Run.RUN_ID == User_Event_Activity.RUN_ID). \
                    filter(Run.RUN_ID == run_id).first()
    user_club_run = db.query(User_Club_Activity). \
                    join(Run, Run.RUN_ID == User_Club_Activity.RUN_ID). \
                    filter(Run.RUN_ID == run_id).first()
    try:

        # Kiểm tra xem người dùng hiện tại có phải admin hay ko
        user_roles = db.query(User_Role).filter(
            User_Role.USER_ID == current_user.USER_ID
        ).all()

        user_role_ids = [user_role.ROLE_ID for user_role in user_roles]

        if 1 in user_role_ids:  
            run.STATUS = 1
            run.REASON = reason
            if user_event_run:
                user_event_run.STATUS = 1
            if user_club_run:
                user_club_run.STATUS = 1
            db.commit()
             #cập nhật user
            update_user_ranking_by_id(db, user.USER_ID)
            
            # cập nhật event
            update_ranking_user_event(db)
            update_ranking_event(db)
            # cập nhật club
            update_user_club_distance_and_pace(db)
            update_user_club_ranking(db)
            calculate_club_total_distance(db)
            update_club_ranking(db)

            db.commit()
            return {"message": "Mở khóa hoạt động thành công!"}
        else:
            raise HTTPException(status_code=403, detail="Lỗi trong quá trình mở khóa hoạt động! Vui lòng liên hệ quản trị hệ thống để được hỗ trợ!")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()

#tung.nguyenson11 Hàm đồng bộ dữ liệu theo thời gian cụ thể 08/10/2023
def add_all_activities_by_time(user_activities, db: Session, current_user: User, minutes: int):
    # Tính thời điểm hiện tại
    current_time = datetime.now()

    # Tính thời điểm bắt đầu khoảng thời gian cần lấy dữ liệu
    start_time = current_time - timedelta(minutes=minutes)
    for activity in user_activities:
        start_date_local = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
        if start_date_local < current_user.CREATED_AT:
            continue
        if start_date_local >= start_time and start_date_local <= current_time:
            pace = float(60 / (activity['average_speed'] * 3.6)) if activity['average_speed'] != 0 and activity['average_speed'] is not None else 0
            run = db.query(Run).filter(Run.STRAVA_RUN_ID == activity['id']).first()
            if run is None:
                new_run = Run(
                        USER_ID = current_user.USER_ID,
                        STRAVA_RUN_ID = activity['id'],
                        NAME = activity['name'],
                        DISTANCE = activity['distance']/1000,        
                        DURATION = format_seconds(activity['moving_time']),
                        PACE = pace,
                        CALORI = activity.get('calories',None),
                        CREATED_AT = start_date_local,
                        STATUS=check_pace(pace),
                        TYPE = activity['type'],
                        HEART_RATE=activity.get('average_heartrate', None),
                        STEP_RATE=activity.get('step_rate', None),
                        SUMMARY_POLYLINE =activity['map']['summary_polyline']   
                    )
                db.add(new_run)    
    db.commit()

#tung.nguyenson11 Hàm đồng bộ dữ liệu theo thời gian cụ thể 08/10/2023
def re_initialize_activities_by_time(db: Session, minutes: int): 
        webhook.router.RE_INIT_STATUS= True
        update_statement = update(User).values(SYNC_STATUS='0')
        db.execute(update_statement)
        db.commit()
        user_list = db.query(User).filter(User.STRAVA_ID.isnot(None)).all()
        for user in user_list:
            try:
                after = int(user.CREATED_AT.timestamp())    
                activity = get_all_activities(user.STRAVA_ACCESS_TOKEN, after)
                if activity is None:
                    access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
                    activity = get_all_activities(access_token, after)
                    user.STRAVA_ACCESS_TOKEN = access_token
                    user.STRAVA_REFRESH_TOKEN = new_refresh_token
                
                add_all_activities_by_time(activity, db, user, minutes)
                update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='1')
                db.execute(update_statement)
                db.commit()
            except:
                db.rollback() 
                update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='-1')
                db.execute(update_statement)
                db.commit()
        try:        
            for data in webhook.temp_data_list:
                if data.aspect_type=='update':
                    update_run_eventwebhook(data,db)
                else :
                    add_run_eventwebhook(data,db)
                
            webhook.temp_data_list.clear()
            sync_runs_to_user_event_activity(db)
            sync_runs_to_user_club_activity(db)

            update_ranking_user_event(db)
            update_user_club_distance_and_pace(db)
            update_user_club_ranking(db)
            calculate_club_total_distance(db)
            update_club_ranking(db)
            update_user_ranking(db)
            update_ranking_event(db)
        except:
            db.rollback() 

        update_statement = update(User).where(User.SYNC_STATUS =='0').values(SYNC_STATUS='-2')
        db.execute(update_statement)
        db.commit()
        webhook.router.RE_INIT_STATUS= False
        print(webhook.router.RE_INIT_STATUS)

def re_initialize_activities_auto(db: Session, scan_time: int):
    webhook.router.RE_INIT_STATUS= True
    update_statement = update(User).values(SYNC_STATUS='0')
    db.execute(update_statement)
    db.commit()
    user_list = db.query(User).filter(User.STRAVA_ID.isnot(None)).all()
    for user in user_list:
        try:
            after = int(user.CREATED_AT.timestamp())    
            activity = get_all_activities(user.STRAVA_ACCESS_TOKEN, after)
            if activity is None:
                access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
                activity = get_all_activities(access_token, after)
                user.STRAVA_ACCESS_TOKEN = access_token
                user.STRAVA_REFRESH_TOKEN = new_refresh_token
            
            add_all_activities_auto(activity, db, user, scan_time)
            update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='1')
            db.execute(update_statement)
            db.commit()
        except:
            db.rollback() 
            update_statement = update(User).where(User.USER_ID == user.USER_ID).values(SYNC_STATUS='-1')
            db.execute(update_statement)
            db.commit()
    # try:          
    for data in webhook.temp_data_list:
        if data.aspect_type=='update':
            update_run_eventwebhook(data,db)
        else :
            add_run_eventwebhook(data,db)
        
    webhook.temp_data_list.clear()
    sync_runs_to_user_event_activity(db)
    sync_runs_to_user_club_activity(db)

    update_ranking_user_event(db)
    update_user_club_distance_and_pace(db)
    update_user_club_ranking(db)
    calculate_club_total_distance(db)
    update_club_ranking(db)
    update_user_ranking(db)
    update_ranking_event(db)
    # except:
    #         db.rollback() 

    update_statement = update(User).where(User.SYNC_STATUS =='0').values(SYNC_STATUS='-2')
    db.execute(update_statement)
    db.commit()
    webhook.router.RE_INIT_STATUS= False
    
def add_all_activities_auto(user_activities, db: Session, current_user: User, scan_time:int):
    # Tính thời điểm hiện tại
    current_time = datetime.now()

    # Tính thời điểm bắt đầu khoảng thời gian cần lấy dữ liệu
    start_time = current_time - timedelta(minutes=scan_time)
    for activity in user_activities:
        start_date_local = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
        if start_date_local < current_user.CREATED_AT:
            continue
        if start_date_local >= start_time and start_date_local <= current_time:
            pace = float(60 / (activity['average_speed'] * 3.6)) if activity['average_speed'] != 0 and activity['average_speed'] is not None else 0
            run = db.query(Run).filter(Run.STRAVA_RUN_ID == activity['id']).first()
            if run is None:
                new_run = Run( 
                        USER_ID = current_user.USER_ID,
                        STRAVA_RUN_ID = activity['id'],
                        NAME = activity['name'],
                        
                        DISTANCE = activity['distance']/1000,        
                        DURATION = format_seconds(activity['moving_time']),
                        PACE = pace,
                        CALORI = activity.get('calories',None),
                        CREATED_AT = start_date_local,
                        STATUS=check_pace(pace),
                        TYPE = activity['type'],
                        HEART_RATE=activity.get('average_heartrate', None),
                        STEP_RATE=activity.get('step_rate', None),
                        SUMMARY_POLYLINE =activity['map']['summary_polyline']   
                    )
                db.add(new_run)    
    db.commit()