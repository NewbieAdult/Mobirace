# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, Query, Form
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, SYSTEM
from auth.oauth2 import get_current_user
from db.db_run import *
from db.db_user import search_user
from typing import Optional
from router import webhook
import threading, asyncio
from utils.base_url import get_base_url
from apscheduler.schedulers.background import BackgroundScheduler
import schedule    
import json
router = APIRouter(
  #prefix='/admin',
  tags=['admin']
)

is_periodic_task_running = False

@router.post('/re-initialize')
async def re_initialize( current_user: User = Depends(get_current_user)):
    if webhook.router.RE_INIT_STATUS:
        return {"status": 200, "detail": "Vui lòng chờ đợi đồng bộ dữ liệu hoàn tất"}
    else:
        db = next(get_db())
        my_thread = threading.Thread(target=re_initialize_activities, args=(db,))
        my_thread.start()
        return {"status": 200, "detail": "Đang khởi tạo lại dữ liệu"}
       
# a activity
@router.post('/re-initialize/user/{id}')
async def re_initialize(id: int,current_user: User = Depends(get_current_user)):
  db = next(get_db())
  user = db.query(User).filter(User.USER_ID == id).first()
  if user.SYNC_STATUS == '0':
    db.close()
    return {"status": 200, "detail": "Vui lòng chờ đợi đồng bộ dữ liệu hoàn tất"}
  else:
    db = next(get_db())
    my_thread = threading.Thread(target=re_initialize_activity, args=(id,db,))
    my_thread.start()
    return {"status": 200, "detail": "Đang khởi tạo lại dữ liệu cho user"}

@router.get('/find-user')
def find_all_user(text_search: Optional[str] = Query(None),per_page : int = Query(10), current_page : int=Query(1),
                        db: Session = Depends(get_db), host: str = Depends(get_base_url)):
   return search_user(host, text_search,per_page,current_page,db)

#tung.nguyenson11 API đồng bộ dữ liệu theo thời gian cụ thể 08/10/2023
@router.post('/re-initialize-by-time')
async def re_initialize_by_time(minutes: int, current_user: User = Depends(get_current_user)):
    if webhook.router.RE_INIT_STATUS:
        return {"status": 200, "detail": f"Vui lòng chờ đợi đồng bộ dữ liệu trong {minutes} phút qua hoàn tất"}
    else:
        db = next(get_db())
        my_thread = threading.Thread(target=re_initialize_activities_by_time, args=(db, minutes))
        my_thread.start()
        return {"status": 200, "detail": "Đang khởi tạo lại dữ liệu"}

# Tạo một APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

def periodic_task(scan_time):
    if webhook.router.RE_INIT_STATUS:
        print("Đang có tiến trình đồng bộ. Vui lòng chờ đợi đồng bộ dữ liệu hoàn tất")
    else:
        db = next(get_db())
        my_thread = threading.Thread(target=re_initialize_activities_auto, args=(db, scan_time))
        my_thread.start()
        print("Tiến trình đồng bộ định thời bắt đầu")

@router.post("/re-initialize-auto")
def start_periodic_task(status: int = Form(None),
                        scan_time: int = Form(None),
                        auto_time: int = Form(None),
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    try:
        if status == 1:
            periodic_task(scan_time)
            # Kiểm tra xem công việc có ID 'periodic_task' có tồn tại không
            job = scheduler.get_job('periodic_task')
            if job:
                job.remove()
                result = "Quá trình cập nhật dữ liệu định thời theo tần suất quét đã cập nhật"
            else:
                result = "Quá trình cập nhật dữ liệu định thời theo tần suất quét bắt đầu"
            scheduler.add_job(
                periodic_task, 'interval', minutes=auto_time,
                args=[scan_time], id='periodic_task'
            )
            system_update = (
                update(SYSTEM)
                .where(SYSTEM.KEY == "STRAVA_SYNC_DATA_SCAN_TIME")
                .values(VALUE=scan_time)
            ) 
            db.execute(system_update)
            system_update = (
                update(SYSTEM)
                .where(SYSTEM.KEY == "STRAVA_SYNC_DATA_AUTO_TIME")
                .values(VALUE=auto_time)
            ) 
            db.execute(system_update)
            system_update = (
                update(SYSTEM)
                .where(SYSTEM.KEY == "STRAVA_SYNC_DATA_STATUS")
                .values(VALUE=status)
            ) 
            db.execute(system_update)
            db.commit()
            return {"message": result}
        elif status == 0:
            system_update = (
                update(SYSTEM)
                .where(SYSTEM.KEY == "STRAVA_SYNC_DATA_STATUS")
                .values(VALUE=status)
            ) 
            db.execute(system_update)
            db.commit()
            job = scheduler.get_job('periodic_task')
            if job:
                job.remove()
                return {"message": "Đã dừng cập nhật dữ liệu định thời theo tần suất quét"}
            return {"message": "Không tồn tại quá trình cập nhật dữ liệu định thời theo tần suất quét"}
        return {"message": "Invalid status value"}
    except Exception as e:
        return {"message": f"Xảy ra lỗi: {str(e)}"}

@router.get("/get-initialize-auto")
def get_task(db: Session = Depends(get_db)):
    status = db.query(SYSTEM.VALUE).filter(SYSTEM.KEY == "STRAVA_SYNC_DATA_STATUS").first()
    auto_time = db.query(SYSTEM.VALUE).filter(SYSTEM.KEY == "STRAVA_SYNC_DATA_AUTO_TIME").first()
    scan_time = db.query(SYSTEM.VALUE).filter(SYSTEM.KEY == "STRAVA_SYNC_DATA_SCAN_TIME").first()
    if status[0]==1:
        return {
                    "status": status[0],
                    "auto_time": auto_time[0],
                    "scan_time": scan_time[0]
                }
    else:
        return {
                    "status": status[0]
                }