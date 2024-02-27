from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from router import area
from router import user, listsize, org, home
from auth import authentication
from router import user, listsize, org, home, picture, avatar, club, post, scoreboard, event,detail_event, strava,run,chart, webhook, slogan,admin
from fastapi.staticfiles import StaticFiles
from db.database import engine
import images
from fastapi.responses import FileResponse

from db.database import get_db
app = FastAPI()
param = "mrun_be"
# note
list_router = [
    area.router,
    user.router,
    listsize.router,
    org.router, 
    home.router,
    authentication.router,
    avatar.router,
    picture.router,
    club.router,
    scoreboard.router,
    event.router,
    detail_event.router,
    strava.router,
    run.router,
    post.router,
    chart.router,
    webhook.router,
    slogan.router,
    admin.router,
    images.router
]
for router in list_router:
      app.include_router(router,prefix=f"/{param}")

origins = ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)
app.mount(f'/{param}/images',StaticFiles(directory="images"),name='images')
