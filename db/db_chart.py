from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Run,User, User_Club_Activity, User_Event_Activity, UserEvent, User_Club
from sqlalchemy import func,extract
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Hàm lấy thông tin hoạt động trong 14 ngày gần nhất cho đến hiện tại tung.nguyenson11 03/10/2023
def get_by_day(db:Session,user_id:int):
    try:
        current_date = datetime.now()
        user_created_date = db.query(User.CREATED_AT).filter(User.USER_ID == user_id).first()
        user_created_date = user_created_date[0]
        start_date = current_date - timedelta(days=14)
        time_difference  = current_date - start_date
        time_set = time_difference.days
        if user_created_date >= start_date:
            start_date = user_created_date
            time_difference = current_date - user_created_date 
            time_set = time_difference.days 
        
        date_list = []
        result = db.query(
                func.date(Run.CREATED_AT).label('datetime'),
                func.sum(Run.DISTANCE).label('date_distance'),
                func.avg(Run.PACE).label('date_pace')
            ).filter(
                Run.USER_ID == user_id,
                Run.CREATED_AT >= start_date,
                Run.CREATED_AT <= current_date,
                Run.STATUS == '1'
            ) \
            .order_by("datetime") \
            .group_by(func.date(Run.CREATED_AT)).all()
        
        for i in range(time_set+2):
            date = start_date + timedelta(days=i)
            if date<=current_date:
                formatted_date = date.strftime('%d/%m')
                date_item = {
                    'datetime': formatted_date,
                    'date_distance': 0,  
                    'date_pace': 0
                }
                for row in result:
                    if row.datetime.strftime('%d/%m') == formatted_date:
                        date_item['date_distance'] = row.date_distance
                        date_item['date_pace'] = row.date_pace
                    
                date_list.append(date_item)

        return date_list
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Biểu đồ ngày hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    finally:
        db.close()
        
def get_by_month(db: Session,user_id:int):
    try:
        current_month = datetime.now()
        user_created_date = db.query(User.CREATED_AT).filter(User.USER_ID == user_id).first()
        user_created_date = user_created_date[0]
        start_month = current_month - relativedelta(months=12)
        time_difference_month = 11
        if user_created_date >= start_month:
            start_month = user_created_date
            time_difference= relativedelta(current_month, user_created_date)
            time_difference_month = time_difference.months
        
        result = db.query(
            extract('month', Run.CREATED_AT).label('month'),
            extract('year', Run.CREATED_AT).label('year'),
            func.sum(Run.DISTANCE).label('month_distance'),
            func.avg(Run.PACE).label('month_pace')
        ).filter(Run.USER_ID==user_id, Run.STATUS == '1',
                Run.CREATED_AT >= start_month,
                Run.CREATED_AT <= current_month) \
        .order_by("year", "month") \
        .group_by(extract('month', Run.CREATED_AT), extract('year', Run.CREATED_AT)).all()

        summary_list = []     
        for i in range(time_difference_month + 1):
            month = start_month + relativedelta(months=i)
            formatted_date = month.strftime('%m/%y')
            date_item = {
                'month_time': formatted_date,
                'month_distance': 0,  
                'month_pace': 0
            }
            for row in result:
                if str(row.month).zfill(2) == month.strftime('%m') and str(row.year)[-2:] == month.strftime('%y'):
                    date_item['month_distance'] = row.month_distance
                    date_item['month_pace'] = row.month_pace

            summary_list.append(date_item)

        return summary_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Biểu đồ tháng hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
        
# Hàm lấy thông tin hoạt động của club-id trong 14 ngày gần nhất cho đến hiện tại thien.tranthi 19/10/2023
def get_club_by_day(db:Session,user_id:int, club_id: int):
    try:
        current_date = datetime.now()
        # user_created_date = db.query(User.CREATED_AT).filter(User.USER_ID == user_id).first()
        # tung.nguyenson11 chỉnh lại công thức lấy biểu đồ ngày 25/10/2023
        user_created_date = db.query(User_Club.c.JOIN_DATE).filter(User_Club.c.USER_ID == user_id, User_Club.c.CLUB_ID == club_id).first()
        user_created_date = user_created_date[0]
        start_date = current_date - timedelta(days=14)
        time_difference  = current_date - start_date
        time_set = time_difference.days
        if user_created_date >= start_date:
            # start_date = user_created_date.replace(hour=current_date.hour, minute=current_date.minute, second=current_date.second)
            # tung.nguyenson11 chỉnh lại công thức lấy biểu đồ ngày 25/10/2023
            start_date = user_created_date
            time_difference = current_date - start_date 
            time_set = time_difference.days + 1
        
        date_list = []
        result = db.query(
                func.date(User_Club_Activity.CREATED_AT).label('datetime'),
                func.sum(User_Club_Activity.DISTANCE).label('date_distance'),
                func.avg(User_Club_Activity.PACE).label('date_pace')
            ).filter(
                User_Club_Activity.USER_ID == user_id,
                User_Club_Activity.CLUB_ID == club_id,
                User_Club_Activity.CREATED_AT >= start_date,
                User_Club_Activity.CREATED_AT <= current_date,
                User_Club_Activity.STATUS == '1'
            ) \
            .order_by("datetime") \
            .group_by(func.date(User_Club_Activity.CREATED_AT)).all()
        for i in range(time_set+1):
            date = start_date + timedelta(days=i)
            if date<=current_date or date > start_date:
                formatted_date = date.strftime('%d/%m')
                date_item = {
                    'datetime': formatted_date,
                    'date_distance': 0,  
                    'date_pace': 0
                }
                for row in result:
                    if row.datetime.strftime('%d/%m') == formatted_date:
                        date_item['date_distance'] = row.date_distance
                        date_item['date_pace'] = row.date_pace
                    
                date_list.append(date_item)

        return date_list
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Biểu đồ ngày hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    finally:
        db.close()
# Hàm lấy thông tin hoạt động của club-id theo tháng thien.tranthi 19/10/2023       
def get_club_by_month(db: Session,user_id:int, club_id: int):
    try:
        current_month = datetime.now()
        # user_created_date = db.query(User.CREATED_AT).filter(User.USER_ID == user_id).first()
        # tung.nguyenson11 chỉnh lại công thức lấy biểu đồ ngày 25/10/2023
        user_created_date = db.query(User_Club.c.JOIN_DATE).filter(User_Club.c.USER_ID == user_id, User_Club.c.CLUB_ID == club_id).first()
        user_created_date = user_created_date[0]
        start_month = current_month - relativedelta(months=12)
        time_difference_month = 11
        if user_created_date >= start_month:
            start_month = user_created_date
            time_difference= relativedelta(current_month, user_created_date)
            time_difference_month = time_difference.months
        
        result = db.query(
            extract('month', User_Club_Activity.CREATED_AT).label('month'),
            extract('year', User_Club_Activity.CREATED_AT).label('year'),
            func.sum(User_Club_Activity.DISTANCE).label('month_distance'),
            func.avg(User_Club_Activity.PACE).label('month_pace')
        ).filter(User_Club_Activity.USER_ID==user_id, 
                User_Club_Activity.CLUB_ID == club_id,
                User_Club_Activity.STATUS == '1',
                User_Club_Activity.CREATED_AT >= start_month,
                User_Club_Activity.CREATED_AT <= current_month) \
        .order_by("year", "month") \
        .group_by(extract('month', User_Club_Activity.CREATED_AT), extract('year', User_Club_Activity.CREATED_AT)).all()

        summary_list = []     
        for i in range(time_difference_month + 1):
            month = start_month + relativedelta(months=i)
            formatted_date = month.strftime('%m/%y')
            date_item = {
                'month_time': formatted_date,
                'month_distance': 0,  
                'month_pace': 0
            }
            for row in result:
                if str(row.month).zfill(2) == month.strftime('%m') and str(row.year)[-2:] == month.strftime('%y'):
                    date_item['month_distance'] = row.month_distance
                    date_item['month_pace'] = row.month_pace

            summary_list.append(date_item)

        return summary_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Biểu đồ tháng hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# Hàm lấy thông tin biểu đồ hoạt động của thành viên giải chạy trong 14 ngày gần nhất cho đến hiện tại tung.nguyenson11 24/10/2023
def get_event_by_day(db:Session,user_id:int, event_id: int):
    try:
        current_date = datetime.now()
        user_created_date = db.query(UserEvent.JOIN_DATE).filter(UserEvent.USER_ID == user_id, UserEvent.EVENT_ID == event_id).first()
        user_created_date = user_created_date[0]
        start_date = current_date - timedelta(days=14)
        time_difference  = current_date - start_date
        time_set = time_difference.days
        if user_created_date >= start_date:
            # start_date = user_created_date.replace(hour=current_date.hour, minute=current_date.minute, second=current_date.second)
            start_date = user_created_date
            time_difference = current_date - user_created_date 
            time_set = time_difference.days + 1
        date_list = []
        result = db.query(
                func.date(User_Event_Activity.CREATED_AT).label('datetime'),
                func.sum(User_Event_Activity.DISTANCE).label('date_distance'),
                func.avg(User_Event_Activity.PACE).label('date_pace')
            ).filter(
                User_Event_Activity.USER_ID == user_id,
                User_Event_Activity.EVENT_ID == event_id,
                User_Event_Activity.CREATED_AT >= start_date,
                User_Event_Activity.CREATED_AT <= current_date,
                User_Event_Activity.STATUS == '1'
            ) \
            .order_by("datetime") \
            .group_by(func.date(User_Event_Activity.CREATED_AT)).all()
        for i in range(time_set+1):
            date = start_date + timedelta(days=i)
            if date<=current_date or date > start_date:
                formatted_date = date.strftime('%d/%m')
                date_item = {
                    'datetime': formatted_date,
                    'date_distance': 0,  
                    'date_pace': 0
                }
                for row in result:
                    if row.datetime.strftime('%d/%m') == formatted_date:
                        date_item['date_distance'] = row.date_distance
                        date_item['date_pace'] = row.date_pace
                    
                date_list.append(date_item)

        return date_list
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Biểu đồ ngày hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    finally:
        db.close()
# Hàm lấy thông tin biểu đồ hoạt động của thành viên giải chạy trong 12 tháng gần nhất cho đến hiện tại tung.nguyenson11 24/10/2023    
def get_event_by_month(db: Session,user_id:int, event_id: int):
    try:
        current_month = datetime.now()
        user_created_date = db.query(UserEvent.JOIN_DATE).filter(UserEvent.USER_ID == user_id, UserEvent.EVENT_ID == event_id).first()
        user_created_date = user_created_date[0]
        start_month = current_month - relativedelta(months=12)
        time_difference_month = 11
        if user_created_date >= start_month:
            start_month = user_created_date
            time_difference= relativedelta(current_month, user_created_date)
            time_difference_month = time_difference.months
        
        result = db.query(
            extract('month', User_Event_Activity.CREATED_AT).label('month'),
            extract('year', User_Event_Activity.CREATED_AT).label('year'),
            func.sum(User_Event_Activity.DISTANCE).label('month_distance'),
            func.avg(User_Event_Activity.PACE).label('month_pace')
        ).filter(User_Event_Activity.USER_ID==user_id, 
                User_Event_Activity.EVENT_ID == event_id,
                User_Event_Activity.STATUS == '1',
                User_Event_Activity.CREATED_AT >= start_month,
                User_Event_Activity.CREATED_AT <= current_month) \
        .order_by("year", "month") \
        .group_by(extract('month', User_Event_Activity.CREATED_AT), extract('year', User_Event_Activity.CREATED_AT)).all()

        summary_list = []     
        for i in range(time_difference_month + 1):
            month = start_month + relativedelta(months=i)
            formatted_date = month.strftime('%m/%y')
            date_item = {
                'month_time': formatted_date,
                'month_distance': 0,  
                'month_pace': 0
            }
            for row in result:
                if str(row.month).zfill(2) == month.strftime('%m') and str(row.year)[-2:] == month.strftime('%y'):
                    date_item['month_distance'] = row.month_distance
                    date_item['month_pace'] = row.month_pace

            summary_list.append(date_item)

        return summary_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Biểu đồ tháng hoạt động của người dùng chưa đúng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
        
