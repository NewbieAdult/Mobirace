# tung.nguyenson11 ghi log webhook 10/10/2023
from schemas import WebhookResponse
from sqlalchemy.orm.session import Session
from db.models import Webhook_Log, Webhook_Log_1
from db.database import SessionLocal
from datetime import datetime
from fastapi import HTTPException
import pytz

def write_log(hub_verify_token: str, hub_challenge: str, hub_mode: str):
    db = SessionLocal()
    new_log = Webhook_Log(
            HUB_VERIFY_TOKEN = hub_verify_token,
            HUB_CHALLENGE = hub_challenge,
            HUB_MODE = hub_mode,
            CREATED_AT = datetime.now()
    )
    db.add(new_log)
    db.commit()

def write_webhook_log(aspect_type: str,
              event_time: int,
              object_id: int,
              object_type: str,
              owner_id: int,
              subscription_id: int):
    try:
        db = SessionLocal()
        new_log = Webhook_Log_1(
                ASPECT_TYPE = aspect_type,
                EVENT_TIME = event_time,
                OBJECT_ID = object_id,
                OBJECT_TYPE = object_type,
                OWNER_ID = owner_id,
                SUBSCRIPTION_ID = subscription_id,
                CREATED_AT = datetime.now(pytz.timezone('Asia/Bangkok'))
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=f"{e}")