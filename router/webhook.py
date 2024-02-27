from starlette.requests import Request as StarletteRequest
from fastapi import APIRouter, Request, Depends
from fastapi import HTTPException
from schemas import WebhookResponse
from sqlalchemy.orm import Session
from db.database import get_db
from db.db_webhook_log import write_log, write_webhook_log


router = APIRouter(
#   prefix='/webhook',
  tags=['webhook']
)
VERIFY_TOKEN = "STRAVA"
router.RE_INIT_STATUS = False
temp_data_list = []

@router.get('/webhook')
def verify_webhook(request: Request):
    starlette_request = StarletteRequest(request.scope, request.receive)
    query_params = starlette_request.query_params

    hub_verify_token = query_params.get('hub.verify_token')
    hub_challenge = query_params.get('hub.challenge')
    hub_mode = query_params.get('hub.mode')

    # tung.nguyenson11 ghi log webhook 10/10/2023
    write_log(hub_verify_token, hub_challenge, hub_mode)

    if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
        return {"hub.challenge": hub_challenge}
       
    else:
        raise HTTPException(status_code=403)

@router.post('/webhook')
async def process_webhook(request: Request, db: Session = Depends(get_db)):
    from db.db_run import update_run_eventwebhook, add_run_eventwebhook
    request_body = await request.json()
    res = WebhookResponse(**request_body)
    print(res)
    write_webhook_log(res.aspect_type, 
                      res.event_time, 
                      res.object_id,
                      res.object_type,
                      res.owner_id,
                      res.subscription_id)

    if router.RE_INIT_STATUS == True:
        temp_data_list.append(res)
        return {"status": 200}

    if res.aspect_type=='update':
        update_run_eventwebhook(res,db)
    else :
        add_run_eventwebhook(res,db)
    return {"status": 200}
   


    

 

