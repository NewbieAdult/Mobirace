from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import listsize, area

app = FastAPI()

list_router = [
    area.router,
    listsize.router
]
for router in list_router:
      app.include_router(router,prefix="/mobirun")

origins = ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

#models.Base.metadata.create_all(bind=engine)
