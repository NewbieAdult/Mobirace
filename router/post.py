# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import APIRouter, Depends, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_news
from db.models import User
from schemas import PostDetailAccess, PostOutResponse, PostResponse, PostDetail
from auth.oauth2 import get_current_user
from typing import Optional, Union
from utils.base_url import get_base_url
router = APIRouter(
    prefix='/post',
    tags=['post']
)

@router.get('/', response_model=PostResponse)
def get_all_post_info(search_text: Optional[str] = None,
                      current_page: int = Query(1, alias='current_page'), 
                      per_page: int = Query(5, alias='per_page'), 
                      db: Session = Depends(get_db), 
                      host: str = Depends(get_base_url)):
    return db_news.get_all_posts(host, search_text, current_page=current_page, per_page=per_page, db=db)

@router.get('/post-detail/{post_id}', response_model=PostDetail)
def get_post_by_id(post_id: int, db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_post_detail(host, post_id=post_id, db=db)

@router.get('/detail-post/{post_id}', response_model=PostDetailAccess)
def get_post_detail_access(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_post_detail_access(host, post_id=post_id, current_user=current_user, db=db)

@router.get('/search', response_model=PostResponse)
def search_posts_route(name: str, current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.search_post(host, name=name, current_page=current_page, per_page=per_page, db=db)

@router.post('/add-post')
def create_post_route(  image: UploadFile = File(...),
                        title: str = Form(...),
                        content: Optional[str] = Form(None),
                        description: str = Form(None), 
                        db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db_news.create_post(image=image,title=title,content=content,description=description, db=db, current_user=current_user)

@router.put('/update/{post_id}', status_code=200)
def update_post_route(  post_id: int, 
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        # image: UploadFile = File(...),
                        image: Union[UploadFile,str] = Form(None),
                        title: str = Form(...),
                        content: Optional[str] = Form(None),
                        description: str = Form(None)
                       ):
    return db_news.update_post(post_id, db=db,current_user=current_user, image=image,title=title,content=content,description=description)

@router.put('/delete/{post_id}', status_code=200)
def delete_post_route(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db_news.delete_post(post_id=post_id, current_user=current_user, db=db)

@router.get('/post-me', response_model=PostOutResponse)
def get_own_posts_router(current_user:User=Depends(get_current_user), current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_own_posts(host, current_user=current_user,current_page=current_page, per_page=per_page, db=db)

@router.put('/add-outstanding')
def add_post_outstanding_route(post_id: int, db: Session = Depends(get_db)):
    return db_news.add_post_outstanding(db, post_id)

@router.put('/delete-outstanding')
def delete_post_outstanding_route(post_id: int, db: Session = Depends(get_db)):
    return db_news.delete_post_outstanding(db, post_id)

@router.post("/approve-post/{post_id}")
def approve_post_router(post_id: int, db: Session = Depends(get_db)):
    return db_news.approve_post(post_id, db)

@router.get("/pending-post")
def get_pending_posts_router(current_user:User=Depends(get_current_user), current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_pending_posts(host, current_user=current_user,current_page=current_page, per_page=per_page, db=db)
    
@router.get("/post-pending")
def get_pending_posts_for_admin(current_page: int = Query(1, alias='current_page'),
                               per_page: int = Query(5, alias='per_page'),
                               db: Session = Depends(get_db), 
                               host: str = Depends(get_base_url)):
    return db_news.get_pending_posts_for_admin(host, current_page, per_page, db)

@router.get('/post-exceptional')
def get_exception_post_router(current_page: int = Query(1, alias='current_page'), per_page: int = Query(5, alias='per_page'), db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_exception_post(host, current_page=current_page, per_page=per_page, db=db)

# API lấy danh sách các bài viết nổi bật tung.nguyenson11 22/10/2023
@router.get('/post-outstanding')
def get_post_outstanding(db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_news(host, db)

# API lấy danh sách các bài viết không nổi bật tung.nguyenson11 22/10/2023
@router.get('/post-normal')
def get_post_outstanding(db: Session = Depends(get_db), host: str = Depends(get_base_url)):
    return db_news.get_post_new(host, db)