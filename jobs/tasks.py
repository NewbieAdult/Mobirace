from sqlalchemy import text
from sqlalchemy.sql import func, update, and_, case
from sqlalchemy.orm.session import Session
from db.models import (User, Event, 
                       UserEvent, Run, 
                       Club_Event, User_Club, 
                       Club, User_Event_Activity, 
                       User_Club_Activity, Flaudulent_Activity_Club,
                       Flaudulent_Activity_Event)
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
import logging
def update_user_ranking(db: Session):
    try:
        users = db.query(User).all()

        for user in users:
            runs = db.query(Run).filter(Run.USER_ID == user.USER_ID, Run.STATUS == '1').all()
            
            total_distance = sum(run.DISTANCE for run in runs if run.CREATED_AT > user.CREATED_AT)
            
            avg_pace_runs = [run.PACE for run in runs if run.CREATED_AT > user.CREATED_AT and run.PACE > 4]
            avg_pace = sum(avg_pace_runs) / len(avg_pace_runs) if avg_pace_runs else 0

            user.TOTAL_DISTANCE = total_distance
            user.PACE = avg_pace

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,detail="Cập nhật toàn bộ người dùng bị lỗi! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# tung.nguyenson11 hàm cập nhật user cụ thể theo id 22/09/2023
def update_user_ranking_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.USER_ID == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Người dùng này không tồn tại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    try:
        total_distance = db.query(func.sum(Run.DISTANCE))\
            .filter(Run.USER_ID == user_id, Run.CREATED_AT > user.CREATED_AT, Run.STATUS == "1")\
            .scalar()
        avg_pace = db.query(func.avg(Run.PACE))\
            .filter(Run.USER_ID == user_id, user.CREATED_AT < Run.CREATED_AT, Run.PACE > 4, Run.STATUS == "1")\
            .scalar()
        user.TOTAL_DISTANCE = total_distance if total_distance else 0
        user.PACE = avg_pace if avg_pace else 0

        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500,detail="Cập nhật người dùng bị lỗi! Vui lòng liên hệ quản trị hệ thống để được hỗ trợ!")

#Sinhhung
def update_ranking_user_event(db: Session, event_id: int = None):
    try:
        mysql_query = text("""
            UPDATE USER_EVENT AS ue
            INNER JOIN (
                SELECT 
                    ue.USER_ID,
                    ue.EVENT_ID,
                    COALESCE(SUM(r.DISTANCE), 0) AS total_distance,
                    COALESCE(AVG(r.PACE), 0) AS average_pace,
                    RANK() OVER (PARTITION BY ue.EVENT_ID ORDER BY SUM(r.DISTANCE) DESC, ue.USER_ID) AS ranking
                FROM 
                    USER_EVENT ue 
                INNER JOIN 
                    EVENT e 
                    ON ue.EVENT_ID = e.EVENT_ID
                LEFT JOIN 
                    USER_EVENT_ACTIVITY r 
                    ON ue.USER_ID = r.USER_ID AND r.CREATED_AT BETWEEN ue.JOIN_DATE AND e.END_DATE AND ue.EVENT_ID  = r.EVENT_ID AND r.STATUS ='1'
                WHERE 
                    e.STATUS = '1'  
                    AND (r.PACE IS NULL OR (r.PACE <= e.MAX_PACE and r.PACE >= e.MIN_PACE))
                    AND ue.EVENT_ID = COALESCE(:event_id,ue.EVENT_ID)
                GROUP BY ue.USER_ID, ue.EVENT_ID
            ) AS subquery
            ON ue.USER_ID = subquery.USER_ID AND ue.EVENT_ID = subquery.EVENT_ID
            SET 
                ue.TOTAL_DISTANCE = subquery.total_distance,
                ue.PACE = subquery.average_pace,
                ue.RANKING = subquery.ranking;
        """).bindparams(event_id=event_id)
        db.execute(mysql_query)
        db.commit()
    except SQLAlchemyError as e:
        logging.error("update_ranking_user_event: %s", e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Execution fail: {str(e)}')
    finally:
        db.close()

#Sinhhung
# def update_ranking_club_event(db: Session):
#     try:
#         subquery = db.query(
#             Club_Event.c.CLUB_ID,
#             Club_Event.c.EVENT_ID,
#             func.coalesce(func.sum(Run.DISTANCE), 0).label('total_distance'),
#             func.coalesce(func.avg(Run.PACE), 0).label('average_pace'),
#             func.rank().over(partition_by=Club_Event.c.EVENT_ID, order_by=[func.sum(Run.DISTANCE).desc(), Club_Event.c.CLUB_ID]).label('ranking')
#         ).\
#         join(Event, Club_Event.c.EVENT_ID == Event.EVENT_ID).\
#         join(User_Club, Club_Event.c.CLUB_ID == User_Club.c.CLUB_ID, isouter=True).\
#         outerjoin(Run, (User_Club.c.USER_ID == Run.USER_ID) & Run.CREATED_AT.between(Club_Event.c.JOIN_DATE, Event.END_DATE)).\
#         filter(Event.STATUS == '1',
#                (Run.PACE.is_(None) | (Run.PACE >= Event.MAX_PACE))
#         ).\
#         group_by(Club_Event.c.CLUB_ID, Club_Event.c.EVENT_ID).subquery()

#         update_stmt = (
#             update(Club_Event)
#             .where((Club_Event.c.CLUB_ID == subquery.c.CLUB_ID) & (Club_Event.c.EVENT_ID == subquery.c.EVENT_ID))
#             .values(
#                 {
#                     Club_Event.c.TOTAL_DISTANCE: subquery.c.total_distance,
#                     Club_Event.c.PACE: subquery.c.average_pace,
#                     Club_Event.c.RANKING: subquery.c.ranking
#                 }
#             )
#         )
#         db.execute(update_stmt)
#         db.commit()
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Execution fail: {str(e)}')
#     finally:
#         db.close()

def update_ranking_event(db:Session, event_id: int = None):
    try:
        subquery = (
            db.query(
                Event.EVENT_ID,
                func.sum(UserEvent.TOTAL_DISTANCE).label('total_distance'),
                func.count(UserEvent.USER_ID).label('num_attendee')
            )
            .outerjoin(UserEvent, UserEvent.EVENT_ID == Event.EVENT_ID)
            .filter(UserEvent.JOIN_DATE.between(Event.START_DATE, Event.END_DATE),
                    # can.lt comment 15/10/23
                    Event.EVENT_ID == func.coalesce(event_id, Event.EVENT_ID))
            .group_by(Event.EVENT_ID)
            .order_by(func.sum(Event.TOTAL_DISTANCE).desc())
            .all()
        )
        
        for row in subquery:
            event_id, total_distance, num_attendee = row
            event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
            if event:
                event.TOTAL_DISTANCE = total_distance if total_distance is not None else 0.0
                event.NUM_OF_ATTENDEE = num_attendee if num_attendee is not None else 0

                # Cập nhật NUM_OF_RUNNER
                num_runner = (
                    db.query(func.count(UserEvent.USER_ID))
                    .filter(UserEvent.EVENT_ID == event_id, UserEvent.TOTAL_DISTANCE > 0)
                    .scalar()
                )
                event.NUM_OF_RUNNER = num_runner if num_runner is not None else 0
        
        db.commit()
    except Exception as e:
        logging.error("update_ranking_event: %s", e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi trong quá trình cập nhật lại các giải chạy! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    finally:
        db.close()

# 1 cập nhật rank của user trong club
def update_user_club_ranking(db: Session, club_id: int = None):
    try:
        # Lấy danh sách các CLUB_ID từ bảng USER_CLUB
        # can.lt add 14/10/23 bổ sung điều kiện đồng bộ lại theo club
        club_ids_query = db.query(User_Club.c.CLUB_ID) \
                            .filter(User_Club.c.CLUB_ID == func.coalesce(club_id, User_Club.c.CLUB_ID)) \
                            .distinct(User_Club.c.CLUB_ID).all()
        club_ids = [club_id for club_id, in club_ids_query]
        for club_id in club_ids:
            ranking_subquery = (
                db.query(
                    User_Club.c.USER_ID,
                    User_Club.c.CLUB_ID,
                    User_Club.c.TOTAL_DISTANCE,
                    func.row_number().over(order_by=User_Club.c.TOTAL_DISTANCE.desc()).label("ranking")
                )
                .filter(User_Club.c.CLUB_ID == club_id)
                .subquery()
            )
            update_query = (
                update(User_Club)
                .where(and_(
                    User_Club.c.USER_ID == ranking_subquery.c.USER_ID,
                    User_Club.c.CLUB_ID == ranking_subquery.c.CLUB_ID
                ))
                .values(RANKING=ranking_subquery.c.ranking)
            )
            db.execute(update_query)
        db.commit()
    except Exception as e:
        logging.error("update_user_club_ranking: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình cập nhật xếp hạng người dùng trong câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# 2 cập nhật rank của tất cả club
def update_club_ranking(db: Session, club_id: int = None):
    try:
        ranked_clubs = (
            db.query(
                Club.CLUB_ID,
                Club.CLUB_TOTAL_DISTANCE,
                func.row_number().over(order_by=Club.CLUB_TOTAL_DISTANCE.desc()).label("CLUB_RANKING")
            )
            # can.lt add 14/10/23 bổ sung điều kiện đồng bộ lại theo club
            .filter(Club.CLUB_ID == func.coalesce(club_id, Club.CLUB_ID))
            .all()
        )
        for ranked_club in ranked_clubs:
            db.query(Club).filter(Club.CLUB_ID == ranked_club.CLUB_ID).update({
                Club.CLUB_RANKING: ranked_club.CLUB_RANKING
            })
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Lỗi trong quá trình cập nhật tất cả câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# 3 tính tổng distance của club
def calculate_club_total_distance(db: Session, club_id: int = None):
    try:
        club_total_distance_query = (
            db.query(
                User_Club.c.CLUB_ID,
                func.sum(User_Club.c.TOTAL_DISTANCE).label("total_distance")
            )
            # can.lt add 14/10/23 bổ sung điều kiện đồng bộ lại theo club
            .filter(User_Club.c.CLUB_ID == func.coalesce(club_id, User_Club.c.CLUB_ID))
            .group_by(User_Club.c.CLUB_ID)
            .subquery()
        )
        # for club in club_total_distance_query:
        #     print(f"club_total_distance_query: {club.total_distance}")
        club_update = (
            update(Club)
            .where(Club.CLUB_ID == club_total_distance_query.c.CLUB_ID)
            .values(CLUB_TOTAL_DISTANCE=club_total_distance_query.c.total_distance)
        ) 
        db.execute(club_update)
        db.commit()
    except Exception:
        logging.error("calculate_club_total_distance: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình tính toán distance câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# 4 Tính distance và avh pace của User club
def update_user_club_distance_and_pace(db: Session, club_id: int = None):
    try:
        user_club_query = (
            db.query(
                User_Club.c.USER_ID,
                User_Club.c.CLUB_ID,
                func.sum(
                    case(
                        (and_(
                            # can.lt comment 14/10/23 column User_Club_Activity.CREATED_AT thêm vào chống cháy
                            #   User_Club_Activity.CREATED_AT > User_Club.c.JOIN_DATE,
                              User_Club_Activity.STATUS == '1', 
                              User_Club_Activity.PACE <= Club.MAX_PACE, 
                              User_Club_Activity.PACE >= Club.MIN_PACE),
                        User_Club_Activity.DISTANCE),
                        else_=0
                    )
                ).label("total_distance"),
                func.avg(
                    case(
                        (and_(
                            # can.lt comment 14/10/23 column User_Club_Activity.CREATED_AT thêm vào chống cháy
                            # User_Club_Activity.CREATED_AT > User_Club.c.JOIN_DATE, 
                              User_Club_Activity.STATUS == '1', 
                              User_Club_Activity.PACE <= Club.MAX_PACE, 
                              User_Club_Activity.PACE >= Club.MIN_PACE),
                        User_Club_Activity.PACE),
                        else_=0
                    )
                ).label("average_pace")
            )
            .outerjoin(User_Club_Activity, and_(User_Club_Activity.USER_ID == User_Club.c.USER_ID, 
                                                User_Club_Activity.STATUS == '1'))
            .join(Club, (User_Club.c.CLUB_ID == Club.CLUB_ID 
                        #can.lt add 14/10/23 bổ sung điều kiện đồng bộ lại theo club
                         and Club.CLUB_ID == func.coalesce(club_id,Club.CLUB_ID)))
            .group_by(User_Club.c.USER_ID, User_Club.c.CLUB_ID).all()
        )

        for user_id, club_id, total_distance, average_pace in user_club_query:
            db.query(User_Club).filter_by(USER_ID=user_id, CLUB_ID=club_id).update({
                User_Club.c.TOTAL_DISTANCE: total_distance,
                User_Club.c.PACE: average_pace
            })
        db.commit()
    except Exception as e:
        logging.error("update_user_club_distance_and_pace: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình tính toán distance và pace của người dùng trong câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
def sync_runs_to_user_event_activity(db: Session):
    try:
        # Lấy danh sách các bản ghi từ bảng Run
        runs = db.query(Run).filter(Run.STATUS == "1").all()

        for run in runs:
            # Lấy danh sách sự kiện tương ứng với USER_ID từ bảng UserEvent
            user_events = (
                db.query(UserEvent)
                .filter(UserEvent.USER_ID == run.USER_ID)
                .filter(UserEvent.JOIN_DATE < run.CREATED_AT)  # Thêm điều kiện JOIN_DATE < CREATED_AT
                .all()
            )

            for user_event in user_events:
                # Kiểm tra xem bản ghi UserEventActivity đã tồn tại chưa
                existing_activity = (
                    db.query(User_Event_Activity)
                    .filter(
                        User_Event_Activity.USER_ID == run.USER_ID,
                        User_Event_Activity.EVENT_ID == user_event.EVENT_ID,
                        User_Event_Activity.RUN_ID == run.RUN_ID,
                    )
                    .first()
                )

                if not existing_activity:
                    # Lấy sự kiện tương ứng với USER_EVENT_ID từ bảng Event
                    event = db.query(Event).get(user_event.EVENT_ID)

                    if event:
                        # Tạo bản ghi UserEventActivity dựa trên dữ liệu từ bảng Run, UserEvent và Event
                        user_event_activity = User_Event_Activity(
                            USER_ID=run.USER_ID,
                            EVENT_ID=event.EVENT_ID,
                            RUN_ID=run.RUN_ID,
                            DISTANCE=run.DISTANCE,
                            PACE=run.PACE,
                            DURATION=run.DURATION,
                            NAME=run.NAME,
                            CREATED_AT=run.CREATED_AT,
                            STATUS=1  # Điều chỉnh trạng thái tùy theo yêu cầu của bạn
                        )

                        db.add(user_event_activity)

        # Lưu các thay đổi vào cơ sở dữ liệu
        db.commit()
        return {"message": "Đồng bộ dữ liệu thành công"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình đồng bộ dữ liệu cho người dùng của giải chạy! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    finally:
        db.close()

def sync_runs_to_user_club_activity(db: Session, club_id: int = None, sync_flaudulent_activity: bool = True):
    try:
        # Lấy danh sách các bản ghi từ bảng Run
        runs = db.query(Run).filter(Run.STATUS == "1").all()

        for run in runs:
            # Lấy danh sách sự kiện tương ứng với USER_ID từ bảng UserEvent
            user_clubs = (
                db.query(User_Club)
                .filter(User_Club.c.USER_ID == run.USER_ID,
                        #can.lt add 15/10/23 bổ sung điều kiện đồng bộ lại theo club
                        User_Club.c.CLUB_ID == func.coalesce(club_id,User_Club.c.CLUB_ID))
                # can.lt comment 14/10/23
                .filter(User_Club.c.JOIN_DATE < run.CREATED_AT)  # Thêm điều kiện JOIN_DATE < CREATED_AT
                .all()
            )

            for user_club in user_clubs:
                existing_activity = (
                    db.query(User_Club_Activity)
                    .filter(
                        User_Club_Activity.USER_ID == run.USER_ID,
                        User_Club_Activity.CLUB_ID == user_club.CLUB_ID,
                        User_Club_Activity.RUN_ID == run.RUN_ID,
                    )
                    .first()
                )
                if not existing_activity:
                    # Lấy sự kiện tương ứng với USER_EVENT_ID từ bảng Event
                    club = db.query(Club).get(user_club.CLUB_ID)
                    if club:
                        #can.lt add 15/10/23
                        status_activity = 1
                        if sync_flaudulent_activity:
                            flaudulentActivity = db.query(Flaudulent_Activity_Club).filter(Flaudulent_Activity_Club.ACTIVITY_ID == run.STRAVA_RUN_ID,
                                                                                        Flaudulent_Activity_Club.CLUB_ID == club.CLUB_ID).first()
                            status_activity = 1 if flaudulentActivity is None else 0
                        # Tạo bản ghi UserEventActivity dựa trên dữ liệu từ bảng Run, UserEvent và Event
                        user_club_activity = User_Club_Activity(
                            USER_ID=run.USER_ID,
                            CLUB_ID=club.CLUB_ID,
                            RUN_ID=run.RUN_ID,
                            DISTANCE=run.DISTANCE,
                            PACE=run.PACE,
                            DURATION=run.DURATION,
                            NAME=run.NAME,
                            CREATED_AT=run.CREATED_AT,
                            # can.lt edit 15/10/23
                            # STATUS=1 # Điều chỉnh trạng thái tùy theo yêu cầu của bạn
                            STATUS=status_activity  # Điều chỉnh trạng thái tùy theo yêu cầu của bạn
                        )

                        db.add(user_club_activity)

        # Lưu các thay đổi vào cơ sở dữ liệu
        db.commit()
        return {"message": "Đồng bộ dữ liệu thành công"}

    except Exception as e:
        logging.error("sync_runs_to_user_club_activity: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình đồng bộ dữ liệu người dùng của câu lạc bộ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    finally:
        db.close()

#tung.nguyenson11  hàm cập nhật lại user trong event 22/09/2023
def update_ranking_user_event_by_id(db: Session, user_id: int):
    try:
        mysql_query = text("""
            UPDATE USER_EVENT AS ue
            INNER JOIN (
                SELECT 
                    ue.USER_ID,
                    ue.EVENT_ID,
                    COALESCE(SUM(r.DISTANCE), 0) AS total_distance,
                    COALESCE(AVG(r.PACE), 0) AS average_pace,
                    RANK() OVER (PARTITION BY ue.EVENT_ID ORDER BY SUM(r.DISTANCE) DESC, ue.USER_ID) AS ranking
                FROM 
                    USER_EVENT ue 
                INNER JOIN 
                    EVENT e 
                    ON ue.EVENT_ID = e.EVENT_ID
                LEFT JOIN 
                    USER_EVENT_ACTIVITY r 
                    ON ue.USER_ID = r.USER_ID AND r.CREATED_AT BETWEEN ue.JOIN_DATE AND e.END_DATE AND ue.EVENT_ID  = r.EVENT_ID AND r.STATUS ='1'
                WHERE 
                    e.STATUS = '1'
                    AND (r.PACE IS NULL OR (r.PACE >= e.MAX_PACE and r.PACE <= e.MIN_PACE))
                    AND ue.USER_ID = :user_id
                GROUP BY ue.USER_ID, ue.EVENT_ID
            ) AS subquery
            ON ue.USER_ID = subquery.USER_ID AND ue.EVENT_ID = subquery.EVENT_ID
            SET 
                ue.TOTAL_DISTANCE = subquery.total_distance,
                ue.PACE = subquery.average_pace,
                ue.RANKING = subquery.ranking;
            WHERE ue.USER_ID = :user_id
        """).params(user_id)
        db.execute(mysql_query)
        db.commit()
        print("2")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Execution fail: {str(e)}')
    finally:
        db.close()

#tung.nguyenson11 hàm cập nhật hoạt động user trong event 22/09/2023
def sync_runs_to_user_event_activity_by_id(db: Session, user_id: int):
    try:
        # Lấy danh sách các bản ghi từ bảng Run
        runs = db.query(Run).filter(Run.USER_ID == user_id, Run.STATUS == "1").all()
        for run in runs:
            # Lấy danh sách sự kiện tương ứng với USER_ID từ bảng UserEvent
            user_events = (
                db.query(UserEvent)
                .filter(UserEvent.USER_ID == run.USER_ID)
                .filter(UserEvent.JOIN_DATE < run.CREATED_AT)  # Thêm điều kiện JOIN_DATE < CREATED_AT
                .all()
            )

            for user_event in user_events:
                # Kiểm tra xem bản ghi UserEventActivity đã tồn tại chưa
                existing_activity = (
                    db.query(User_Event_Activity)
                    .filter(
                        User_Event_Activity.USER_ID == run.USER_ID,
                        User_Event_Activity.EVENT_ID == user_event.EVENT_ID,
                        User_Event_Activity.RUN_ID == run.RUN_ID,
                    )
                    .first()
                )
                if not existing_activity:
                    # Lấy sự kiện tương ứng với USER_EVENT_ID từ bảng Event
                    event = db.query(Event).get(user_event.EVENT_ID)
                    #can.lt add 15/10/23
                    flaudulentActivity = db.query(Flaudulent_Activity_Event).filter(Flaudulent_Activity_Event.ACTIVITY_ID == run.STRAVA_RUN_ID,
                                                                                Flaudulent_Activity_Event.EVENT_ID == event.EVENT_ID).first()
                    status_activity = 1 if flaudulentActivity is None else 0
                    if event:
                        # Tạo bản ghi UserEventActivity dựa trên dữ liệu từ bảng Run, UserEvent và Event
                        user_event_activity = User_Event_Activity(
                            USER_ID=run.USER_ID,
                            EVENT_ID=event.EVENT_ID,
                            RUN_ID=run.RUN_ID,
                            DISTANCE=run.DISTANCE,
                            PACE=run.PACE,
                            DURATION=run.DURATION,
                            NAME=run.NAME,
                            CREATED_AT=run.CREATED_AT,
                            # can.lt edit 15/10/23
                            STATUS=status_activity
                            # STATUS=run.STATUS  # Điều chỉnh trạng thái tùy theo yêu cầu của bạn
                        )

                        db.add(user_event_activity)

        # Lưu các thay đổi vào cơ sở dữ liệu
        db.commit()
        return {"message": "Đồng bộ dữ liệu thành công"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cập nhật hoạt động người dùng trong giải chạy thất bại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    finally:
        db.close()

#tung.nguyenson11 hàm cập nhật event 22/09/2023
def update_ranking_event_by_id(db:Session, user_id: int):
    try:
        subquery = (
            db.query(
                Event.EVENT_ID,
                func.sum(UserEvent.TOTAL_DISTANCE).label('total_distance'),
                func.count(UserEvent.USER_ID).label('num_attendee')
            )
            .outerjoin(UserEvent, UserEvent.EVENT_ID == Event.EVENT_ID)
            .filter(UserEvent.JOIN_DATE.between(Event.START_DATE, Event.END_DATE), UserEvent.USER_ID == user_id)
            .group_by(Event.EVENT_ID)
            .order_by(func.sum(Event.TOTAL_DISTANCE).desc())
            .all()
        )
        
        for row in subquery:
            event_id, total_distance, num_attendee = row
            event = db.query(Event).filter(Event.EVENT_ID == event_id).first()
            if event:
                event.TOTAL_DISTANCE = total_distance if total_distance is not None else 0.0
                event.NUM_OF_ATTENDEE = num_attendee if num_attendee is not None else 0

                # Cập nhật NUM_OF_RUNNER
                num_runner = (
                    db.query(func.count(UserEvent.USER_ID))
                    .filter(UserEvent.EVENT_ID == event_id, UserEvent.TOTAL_DISTANCE > 0)
                    .scalar()
                )
                event.NUM_OF_RUNNER = num_runner if num_runner is not None else 0
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cập nhật giải chạy thất bại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    finally:
        db.close()

#tung.nguyenson11 hàm cập nhật hoạt động của user trong club 24/09/2023
def sync_runs_to_user_club_activity_by_id(db: Session, user_id: int):
    try:
        # Lấy danh sách các bản ghi từ bảng Run
        runs = db.query(Run).filter(Run.USER_ID == user_id).all()

        for run in runs:
            # Lấy danh sách sự kiện tương ứng với USER_ID từ bảng UserEvent
            user_clubs = (
                db.query(User_Club)
                .filter(User_Club.c.USER_ID == run.USER_ID)
                .filter(User_Club.c.JOIN_DATE < run.CREATED_AT)  # Thêm điều kiện JOIN_DATE < CREATED_AT
                .all()
            )

            for user_club in user_clubs:
                existing_activity = (
                    db.query(User_Club_Activity)
                    .filter(
                        User_Club_Activity.USER_ID == run.USER_ID,
                        User_Club_Activity.CLUB_ID == user_club.CLUB_ID,
                        User_Club_Activity.RUN_ID == run.RUN_ID,
                    )
                    .first()
                )


                if not existing_activity:
                    # Lấy sự kiện tương ứng với USER_EVENT_ID từ bảng Event
                    club = db.query(Club).get(user_club.CLUB_ID)

                    if club:
                        # Tạo bản ghi UserEventActivity dựa trên dữ liệu từ bảng Run, UserEvent và Event
                        user_club_activity = User_Club_Activity(
                            USER_ID=run.USER_ID,
                            CLUB_ID=club.CLUB_ID,
                            RUN_ID=run.RUN_ID,
                            DISTANCE=run.DISTANCE,
                            PACE=run.PACE,
                            DURATION=run.DURATION,
                            NAME=run.NAME,
                            CREATED_AT=run.CREATED_AT,
                            STATUS=1  # Điều chỉnh trạng thái tùy theo yêu cầu của bạn
                        )

                        db.add(user_club_activity)

        # Lưu các thay đổi vào cơ sở dữ liệu
        db.commit()
        return {"message": "Đồng bộ dữ liệu thành công"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cập nhật hoạt động người dùng trong club thất bại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    finally:
        db.close()

#tung.nguyenson11 hàm cập nhật user trong club 25/09/2023
def update_user_club_distance_and_pace_by_id(db: Session, user_id: int):
    try:
        user_club_query = (
            db.query(
                User_Club.c.USER_ID,
                User_Club.c.CLUB_ID,
                func.sum(
                    case(
                        (and_(User_Club_Activity.CREATED_AT > User_Club.c.JOIN_DATE, User_Club_Activity.STATUS == '1', User_Club_Activity.PACE >= Club.MAX_PACE, User_Club_Activity.PACE <= Club.MIN_PACE),
                            User_Club_Activity.DISTANCE),
                        else_=0
                    )
                ).label("total_distance"),
                func.avg(
                    case(
                        (and_(User_Club_Activity.CREATED_AT > User_Club.c.JOIN_DATE, User_Club_Activity.STATUS == '1', User_Club_Activity.PACE >= Club.MAX_PACE, User_Club_Activity.PACE <= Club.MIN_PACE),
                            User_Club_Activity.PACE),
                        else_=0
                    )
                ).label("average_pace")
            )
            .outerjoin(User_Club_Activity, and_(User_Club_Activity.USER_ID == User_Club.c.USER_ID, User_Club_Activity.STATUS == '1'))
            .join(Club, User_Club.c.CLUB_ID == Club.CLUB_ID).filter(User_Club.c.USER_ID == user_id)
            .group_by(User_Club.c.USER_ID, User_Club.c.CLUB_ID)
        )
        for u_id, club_id, total_distance, average_pace in user_club_query:
            db.query(User_Club).filter_by(USER_ID=u_id, CLUB_ID=club_id).update({
                User_Club.c.TOTAL_DISTANCE: total_distance,
                User_Club.c.PACE: average_pace
            })
        db.commit()
    except Exception: 
        db.rollback()
        raise HTTPException(status_code=500, detail="Cập nhật người dùng trong club thất bại! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
# tung.nguyenson11 cập nhật rank của user trong club 25/09/2023
def update_user_club_ranking_by_id(db: Session, user_id: int):
    try:
        # Lấy danh sách các CLUB_ID từ bảng USER_CLUB
        club_ids_query = db.query(User_Club.c.CLUB_ID).distinct(User_Club.c.CLUB_ID).filter(User_Club.c.USER_ID == user_id).all()
        club_ids = [club_id for club_id, in club_ids_query]
        for club_id in club_ids:
            ranking_subquery = (
                db.query(
                    User_Club.c.USER_ID,
                    User_Club.c.CLUB_ID,
                    User_Club.c.TOTAL_DISTANCE,
                    func.row_number().over(order_by=User_Club.c.TOTAL_DISTANCE.desc()).label("ranking")
                )
                .filter(User_Club.c.CLUB_ID == club_id)
                .subquery()
            )
            update_query = (
                update(User_Club)
                .where(and_(
                    User_Club.c.USER_ID == ranking_subquery.c.USER_ID,
                    User_Club.c.CLUB_ID == ranking_subquery.c.CLUB_ID
                ))
                .values(RANKING=ranking_subquery.c.ranking)
            )
            db.execute(update_query)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cập nhật xếp hạng của người dùng trong club thất bại! Vui lòng liên hệ quản trị hệ thống để được hỗ trợ!")

# tung.nguyenson11 tính tổng total_distance của club theo user_id 25/09/2023
def calculate_club_total_distance_by_id(db: Session, user_id: int):
    try:
        club_total_distance_query = (
            db.query(
                User_Club.c.CLUB_ID,
                func.sum(User_Club.c.TOTAL_DISTANCE).label("total_distance")
            )
            .filter(User_Club.c.USER_ID == user_id)
            .group_by(User_Club.c.CLUB_ID)
            .subquery()
        )
        club_update = (
            update(Club)
            .where(Club.CLUB_ID == club_total_distance_query.c.CLUB_ID)
            .values(CLUB_TOTAL_DISTANCE=club_total_distance_query.c.total_distance)
        ) 
        db.execute(club_update)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cập nhận tổng khoảng cách của câu lạc bộ thất bại! Vui lòng liên hệ quản trị hệ thống để được hỗ trợ!")
