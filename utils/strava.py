import requests, os
from sqlalchemy.orm import Session
from db.models import User, UserEvent, Run, User_Club,User_Event_Activity,User_Club_Activity
from dotenv import load_dotenv
from sqlalchemy import update, delete
from fastapi import HTTPException
from typing import Optional
load_dotenv()

client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")


def get_all_activities(access_token, after: Optional[int]=None ):

    url = f"https://www.strava.com/api/v3/athlete/activities?after={after}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def exchange_authorization_code(authorization_code: str):
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, data=payload)
    data = response.json()
    print(data)
    return data

def exchange_authorization_code_at(authorization_code:str):
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, data=payload)
    data = response.json()
    access_token = data['access_token']
    return access_token

def revoke_access_token(db: Session, current_user: User):
    try:
        access_token, new_refresh_token = refresh_strava_token(current_user.STRAVA_REFRESH_TOKEN)
        url = "https://www.strava.com/oauth/deauthorize"
        params = {"access_token": access_token}
        response = requests.post(url, params=params)
        if response.status_code == 200:
            db.execute(update(User)
                .where(User.USER_ID == current_user.USER_ID)
                .values(
                    PACE=0,
                    TOTAL_DISTANCE=None,
                    STRAVA_ID=None,
                    STRAVA_ACCESS_TOKEN=None,
                    STRAVA_REFRESH_TOKEN=None,
                    STRAVA_FULL_NAME=None,
                    STRAVA_IMAGE=None
                )
            )
            db.execute(update(User_Club)
                .where(User_Club.c.USER_ID == current_user.USER_ID)
                .values(
                    PACE=None,
                    TOTAL_DISTANCE=None
                )
            )

            db.execute(delete(Run).where(Run.USER_ID == current_user.USER_ID))
            db.execute(delete(User_Event_Activity).where(User_Event_Activity.USER_ID == current_user.USER_ID))
            db.execute(delete(UserEvent).where(UserEvent.USER_ID == current_user.USER_ID))
            db.execute(delete(User_Club_Activity).where(User_Club_Activity.USER_ID == current_user.USER_ID))

            db.commit()
            res = {
                "status": 200,
                "message":"Hủy kết nối thành công"
                }
            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hủy kết nối Strava không thành công! Liên lạc quản trị hệ thống để hỗ trợ!")

def get_activity_info_by_id(object_id: int, access_token: str):
    base_url = "https://www.strava.com/api/v3/activities/"
    url = f"{base_url}{object_id}"
    headers = {
        "Authorization": "Bearer " + access_token
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activity_info = response.json()
        return activity_info
    else:
        print("Lỗi khi lấy thông tin hoạt động người dùng: ", response.status_code)
        return None

def refresh_strava_token(refresh_token: str):
    url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token")
        return access_token, new_refresh_token
    else:
        print("Lỗi khi xác thực refresh_token: ", response.status_code)
        return None