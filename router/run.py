# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, HTTPException,status
from db.db_run import sync_activities
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Run,User
import polyline as polyline_decoder
from sqlalchemy.sql import func
from utils.strava import get_activity_info_by_id, refresh_strava_token
from utils.base_url import get_base_url
from auth.oauth2 import get_current_user
from db import db_run
from typing import Optional
from utils.format import format_seconds
router = APIRouter(
  prefix='/run',
  tags=['run']
)
@router.get("/clone-activities")
def clone_activity(authorization_code:str):
    return sync_activities(authorization_code)

@router.get("/decode_polyline/{run_id}")
def decode_polyline(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.RUN_ID == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.SUMMARY_POLYLINE==None or run.SUMMARY_POLYLINE=='':
        user = db.query(User).join(Run, User.USER_ID==Run.USER_ID).filter(User.USER_ID==run.USER_ID).first()
        activity = get_activity_info_by_id(run.STRAVA_RUN_ID, user.STRAVA_ACCESS_TOKEN)
        if activity == None:
            access_token, new_refresh_token = refresh_strava_token(user.STRAVA_REFRESH_TOKEN)
            activity = get_activity_info_by_id(run.STRAVA_RUN_ID, access_token)
            user.STRAVA_ACCESS_TOKEN = access_token
            user.STRAVA_REFRESH_TOKEN = new_refresh_token
        run.SUMMARY_POLYLINE = activity['map']['polyline']  
    db.commit()
    decoded_coords = polyline_decoder.decode(run.SUMMARY_POLYLINE)
    return decoded_coords

@router.get("/member/{user_id}")
def get_detail_user_activities(user_id:int,
                               current_page: int = 1,
                               per_page: int = 5,
                               db:Session=Depends(get_db), 
                               host: str = Depends(get_base_url)) :  
    run=db.query(User).filter(User.USER_ID==user_id).first()
    run_count=db.query(func.count(Run.RUN_ID)).filter(Run.USER_ID==user_id).scalar()
    image_path = run.AVATAR_PATH.replace("\\", "/")
    avatar_path = f"{host}/{image_path}"
    skip = (current_page - 1) * per_page
    if not run :
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # total_seconds = int((run.PACE if run.PACE is not None else 0) * 60)  # Chuyển đổi thành số giây
    # hours = total_seconds // 3600
    # minutes = (total_seconds % 3600) // 60
    # seconds = total_seconds % 60

    user={
      "user_id":run.USER_ID,
      "fullname":run.FULL_NAME,
      "image":avatar_path,
      "user_total_distance":round(run.TOTAL_DISTANCE ,2) if run.TOTAL_DISTANCE is not None else 0,
    #   "user_total_pace":rf"{hours:02d}:{minutes:02d}:{seconds:02d}",
      "user_total_pace":format_seconds(int((run.PACE if run.PACE is not None else 0) * 60)),
      "user_total_run":run_count,
      "strava_user_link":run.STRAVA_ID
      }     
    
    activities_query = db.query(Run).filter(Run.USER_ID==user_id).order_by(Run.CREATED_AT.desc()).offset(skip).limit(per_page).all()

    activities = []
    for activity in activities_query:
        # total_seconds = int((activity.PACE if activity.PACE is not None else 0) * 60)  # Chuyển đổi thành số giây
        # hours = total_seconds // 3600
        # minutes = (total_seconds % 3600) // 60
        # seconds = total_seconds % 60

        activity_info = {
            "activity_id": activity.RUN_ID,
            "activity_start_date": activity.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
            "activity_name": activity.NAME,
            "activity_distance": round(activity.DISTANCE ,2) if activity.DISTANCE is not None else 0,
            # "activity_pace": round(activity.PACE , 2) if activity.PACE is not None else 0,
            "activity_pace": format_seconds(int((activity.PACE if activity.PACE is not None else 0) * 60)),
            "time_finish": activity.DURATION,
            "activity_type": activity.TYPE,
            "calo": activity.CALORI,
            "heart_beat": activity.HEART_RATE,
            "step": activity.STEP_RATE,
            "activity_map": activity.SUMMARY_POLYLINE,
            "activity_link_stava": activity.STRAVA_RUN_ID,
            "activity_status": activity.STATUS,
            "activity_reason": activity.REASON
        }
        activities.append(activity_info)
    total_activities = db.query(func.count(Run.RUN_ID)).filter(Run.USER_ID == user_id).scalar()
    total_pages_activity = (total_activities + per_page - 1) // per_page
    
    table_activities = {
        "per_page_activity": per_page,
        "current_page_activity": current_page,
        "total_page_activity": total_activities,
        "total_page": total_pages_activity,
        "activities": activities
    }
    
    return {"user": user, "table_activities": table_activities}

@router.put("/lock_activity")
def lock_activity(run_id: int, db: Session = Depends(get_db), current_user:User=Depends(get_current_user), reason: Optional[str] = None):
    return db_run.hide_activity(run_id=run_id,db=db,current_user=current_user, reason=reason)

@router.put("/re_lock_activity")
def re_delete_activeevent(run_id: int ,db: Session = Depends(get_db),current_user:User=Depends(get_current_user), reason: Optional[str] = None):
    return db_run.re_hide_activity(run_id=run_id,db=db,current_user=current_user, reason=reason)