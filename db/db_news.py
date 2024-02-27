# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from fastapi import HTTPException, Query, Depends, Form, UploadFile, File
from sqlalchemy.orm.session import Session
from auth.oauth2 import get_current_user
from db.models import Post, User, Log_Post
from math import ceil
from schemas import News, PostDetailAccess, PostOutBase, PostOutResponse, PostResponse, PostBase, PostDetail
from db.database import get_db
from datetime import datetime
from sqlalchemy import desc 
from typing import Optional, Union
import os, shutil
import pytz

#get news
def get_news(host: str, db: Session):
    try:
        news = db.query(Post).filter(
            Post.OUTSTANDING == 1,
            Post.STATUS == 1
        ).order_by(Post.OUTSTANDING.desc(),Post.OUTSTANDING_AT.desc(),Post.CREATED_AT.desc()).all()
        
        news_data = []
        for new in news:
            image_path = new.IMAGE.replace("\\", "/")
            user = db.query(User).filter(User.USER_ID == new.USER_CREATE).first()
            news_item = News(
                POST_ID=new.POST_ID,
                TITLE=new.TITLE,
                IMAGE=f"{host}/{image_path}",
                USER_CREATE =user.FULL_NAME,
                CREATED_AT =new.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
                # HTML_CONTENT =new.HTML_CONTENT,
                OUTSTANDING =new.OUTSTANDING,
                DESCRIPTION=new.DESCRIPTION,
                UPDATE_AT =new.UPDATE_AT.strftime("%d-%m-%Y %H:%M:%S"),
                STATUS =new.STATUS,
                STATUS_NAME="chờ duyệt" if new.STATUS==0 else "đã duyệt",
                OUTSTANDING_NAME="không nổi bật" if new.OUTSTANDING==0 else "nổi bật"
            )
            news_data.append(news_item)
        
        return news_data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi hiển thị các bài viết nổi bật! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def get_all_posts(host: str, 
                  search_text: Optional[str] = None,
                  current_page: int = Query(1, alias='current_page'),
                  per_page: int = Query(5, alias='per_page'),
                  db: Session = Depends(get_db)):
    try:
        skip = (current_page - 1) * per_page
        posts = db.query(Post).filter(Post.STATUS != -1)
        total_posts = len(posts.all())
        if (search_text != 'undefined' and search_text != '') and search_text is not None:
            posts = posts \
                .filter(
                Post.TITLE.ilike(f"%{search_text}%")
            )
            # total_posts = db.query(Post).filter(
            #     Post.TITLE.ilike(f"%{search_text}%"),
            #     Post.STATUS != -1
            # ).count()
            total_posts = len(posts.all())
        # else:
        #     total_posts = db.query(Post).filter(Post.STATUS != -1).count()
        
        posts = posts \
                    .order_by(Post.OUTSTANDING.desc(),Post.OUTSTANDING_AT.desc(),Post.CREATED_AT.desc()).offset(skip).limit(per_page).all()
        all_posts = []
        for post in posts:
            user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
            if user:
                image_path = post.IMAGE.replace("\\", "/")
                post_data = PostBase(
                    id=post.POST_ID,
                    title=post.TITLE,
                    image=f"{host}/{image_path}",
                    description=post.DESCRIPTION,
                    # content=post.HTML_CONTENT,
                    created_at=post.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
                    user_create=user.FULL_NAME,
                    outstanding =post.OUTSTANDING,
                    update_at =post.UPDATE_AT.strftime("%d-%m-%Y %H:%M:%S"),
                    status =post.STATUS,
                    status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                    outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
                )
                all_posts.append(post_data)
        total_page = ceil(total_posts / per_page)
        return PostResponse(
            per_page=per_page,
            current_page=current_page,
            total_page=total_page,
            total_post=total_posts,
            posts=all_posts,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị tất cả bài viết! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def get_post_detail(host: str, post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.POST_ID == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    if post.STATUS == 0:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập bài viết chờ duyệt")
    try:
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        image_path = post.IMAGE.replace("\\", "/")
        post_detail = PostDetail(
            id=post.POST_ID,
            title=post.TITLE,
            image=f"{host}/{image_path}",
            description=post.DESCRIPTION,
            created_at=post.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
            content=post.HTML_CONTENT,
            user_create =user.FULL_NAME,
            outstanding =post.OUTSTANDING,
            update_at =post.UPDATE_AT.strftime("%d-%m-%Y %H:%M:%S"),
            status =post.STATUS,
            status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
            outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
        )
        return post_detail
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị chi tiết bài viết! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def get_post_detail_access(host: str, post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.POST_ID == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")
    is_admin = current_user.USER_ID == post.USER_CREATE
    if not is_admin and post.STATUS == 0:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập bài viết chờ duyệt")
    try:
        image_path = post.IMAGE.replace("\\", "/")
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        post_detail_acc = PostDetailAccess(
            is_admin=is_admin,
            id=post.POST_ID,
            title=post.TITLE,
            image=f"{host}/{image_path}",
            description=post.DESCRIPTION,
            created_at=post.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
            content=post.HTML_CONTENT,
            user_create=user.FULL_NAME,
            outstanding=str(post.OUTSTANDING),
            update_at =post.UPDATE_AT.strftime("%d-%m-%Y %H:%M:%S"),
            status=str(post.STATUS),
            status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
            outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
        )
        return post_detail_acc
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi hiển thị chi tiết bài viết đã duyệt! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def search_post(host: str, name: str, per_page: int, current_page: int, db: Session):
    try:
        offset = (current_page - 1) * per_page
        posts = db.query(Post).filter(
            Post.TITLE.ilike(f"%{name}%"),
            Post.STATUS != -1
        )
        total_posts = posts.count()
        posts = posts.offset(offset).limit(per_page).all()

        all_posts = []
        for post in posts:
            image_path = post.IMAGE.replace("\\", "/")
            user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
            if user:
                post_data = PostBase(
                    id=post.POST_ID,
                    title=post.TITLE,
                    image=f"{host}/{image_path}",
                    description=post.DESCRIPTION,
                    created_at=post.CREATED_AT,
                    updated_at=post.UPDATE_AT,
                    user_create=user.FULL_NAME,
                    status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                    outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
                )
                all_posts.append(post_data)

        total_page = ceil(total_posts / per_page)
        return PostResponse(
            per_page=per_page,
            current_page=current_page,
            total_page=total_page,
            total_post=total_posts,
            posts=all_posts,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi tìm kiếm bài viết! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def create_post(db: Session, current_user: User,
                image: UploadFile = File(...),
                title: str = Form(...),
                content: Optional[str] = Form(None),
                description: str = Form(None)
                ):
    try:
        existing_post = db.query(Post).filter(Post.TITLE == title).first()
        if existing_post:
            raise HTTPException(status_code=400, detail="Bài viết đã tồn tại")


        formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename= f"post_add_{formatted_date}.jpg"

        with open(os.path.join("images", filename), "wb") as f:
            shutil.copyfileobj(image.file, f)

        image_path = os.path.join('images', filename)
        

        created_at = datetime.now()
        update_at = datetime.now()
        add_post = Post(
            TITLE=title,
            DESCRIPTION=description,
            HTML_CONTENT=content,
            IMAGE=image_path,
            USER_CREATE=current_user.USER_ID,
            CREATED_AT=created_at,
            UPDATE_AT=update_at
        )
        db.add(add_post)
        db.commit()
        db.refresh(add_post)
        return {"status": 200, "detail": "Tạo bài viết thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Có lỗi trong quá trình thực hiện:")

def update_post(post_id: int, 
                db: Session, 
                current_user: User,
                image: Union[UploadFile,str] = Form(None),
                title: str = Form(...),
                content: Optional[str] = Form(None),
                description: str = Form(None)):
    
    existing_post = db.query(Post).filter(Post.POST_ID == post_id, Post.STATUS == 1).first()
    if not existing_post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    try:
        if image != 'null':
            formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename= f"post_add_{formatted_date}.jpg"
            with open(os.path.join("images", filename), "wb") as f:
                shutil.copyfileobj(image.file, f)
            
            image_path_new = os.path.join('images', filename)

            title_before = existing_post.TITLE
            description_before = existing_post.DESCRIPTION
            content_before = existing_post.HTML_CONTENT
            image_before = existing_post.IMAGE

            update_data = {
                "TITLE": title,
                "HTML_CONTENT": content,
                "IMAGE":image_path_new ,
                "DESCRIPTION": description,
                "UPDATE_AT": datetime.now()
            }
            db.query(Post).filter(Post.POST_ID == post_id).update(update_data)
            create_log_post(db, post_id, title,description,content,image_path_new, current_user, "modify", title_before, description_before, content_before, image_before)
            db.commit()
        else:        
            title_before = existing_post.TITLE
            description_before = existing_post.DESCRIPTION
            content_before = existing_post.HTML_CONTENT
            image_before = existing_post.IMAGE

            update_data = {
                "TITLE": title,
                "HTML_CONTENT": content,
                "IMAGE": existing_post.IMAGE,
                "DESCRIPTION": description,
                "UPDATE_AT": datetime.now()
            }
            db.query(Post).filter(Post.POST_ID == post_id).update(update_data)
            # create_log_post(db, post_id, title,description,content,image_before, current_user, "modify", title_before, description_before, content_before, image_before)
            db.commit()   
        return {"status": 200, "detail": "Cập nhật bài viết thành công"}
        
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="Có lỗi trong quá trình thực hiện cập nhật 1 2 3") 

def create_log_post(db: Session, post_id: int, 
                    image: str,
                    title: str,
                    content: str,
                    description: str, 
                    current_user: User,
                    action: str, title_before: str, description_before: str,
                    content_before: str, image_before: str):
    log = Log_Post(
        POST_ID=post_id,
        ACTION=action,
        TITLE_BEFORE=title_before,
        DESCRIPTION_BEFORE=description_before,
        CONTENT_BEFORE=content_before,
        IMAGE_BEFORE=image_before,
        TITLE_AFTER=title if title else None,
        DESCRIPTION_AFTER=description if description else None,
        CONTENT_AFTER=content if content else None,
        IMAGE_AFTER=image if image else None,
        USER_MODIFY=current_user.USER_ID,
        CREATED_AT=datetime.now()
    )
    db.add(log)
    db.commit()

def delete_post(post_id: int, current_user: User, db: Session):
    existing_post = db.query(Post).filter(Post.POST_ID == post_id).first()
    if not existing_post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    try:
        db.query(Post).filter(Post.POST_ID == post_id).update({"STATUS": -1})
        db.commit()
        db.close()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Xóa giải chạy không thành công! Vui lòng kiểm tra lại!") 

    return {"status": 200, "detail": "Xóa bài viết thành công"}

def get_own_posts(host: str, current_user: User, db: Session, current_page: int, per_page: int):
    skip = (current_page - 1) * per_page
    total_posts = db.query(Post).filter(
        Post.USER_CREATE == current_user.USER_ID,
        Post.STATUS != -1
    ).count()
    posts = db.query(Post).filter(
        Post.USER_CREATE == current_user.USER_ID,
        Post.STATUS != -1
    ).order_by(desc(Post.CREATED_AT)).offset(skip).limit(per_page).all()
    all_posts = []
    for post in posts:
        image_path = post.IMAGE.replace("\\", "/")
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        
        if user:
            post_data = PostOutBase(
                id=post.POST_ID,
                title=post.TITLE,
                image=f"{host}/{image_path}",
                description=post.DESCRIPTION,
                created_at=post.CREATED_AT,
                updated_at=post.UPDATE_AT,
                user_create=user.FULL_NAME,
                outstanding=post.OUTSTANDING,
                status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
            )
            all_posts.append(post_data)
    total_page = ceil(total_posts / per_page)
    return PostOutResponse(
        per_page=per_page,
        current_page=current_page,
        total_page=total_page,
        total_post=total_posts,
        posts=all_posts,
    )

def add_post_outstanding(db: Session, post_id: int):
    post = db.query(Post).filter(Post.POST_ID == post_id).first()
    
    if post:
        if post.OUTSTANDING  == 0 and post.STATUS == 1:
            post.OUTSTANDING = 1
            post.OUTSTANDING_AT = datetime.now(pytz.timezone('Asia/Bangkok'))
            db.commit()
            return {"status": 200, "detail": "Thêm bài viết nổi bật thành công"}
        else:
            raise HTTPException(status_code=500, detail="Bài viết hiện tại đang là bài viết nổi bật hoặc không hợp lệ! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    else:
        raise HTTPException(status_code=400, detail="Bài viết không tồn tại!")
    
def delete_post_outstanding(db: Session, post_id: int):
    post = db.query(Post).filter(Post.POST_ID == post_id).first()
    
    if post is None:
        raise HTTPException(status_code=404, detail="Bài viêt không tồn tại!")
    
    if post.OUTSTANDING == 1 and post.STATUS == 1:
        post.OUTSTANDING = 0
        db.commit()
        return {"status": 200, "detail": "Bỏ bài viết khỏi nổi bật thành công"}
    else:
        raise HTTPException(status_code=500, detail="Không cần thay đổi trạng thái vì bài viết hiện tại đã duyệt hoặc chưa duyệt! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")
    
def approve_post(post_id: int, db: Session):
    post = db.query(Post).filter(Post.POST_ID == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")

    if post.STATUS == 0:
        post.STATUS = 1
        db.commit()
        return {"status":200,"message": "Duyệt bài viết thành công"}
    else:
        raise HTTPException(status_code=500, detail="Bài viết không ở trạng thái chờ duyệt! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

# lấy bài viết đang chờ duyệt của admin thường 
def get_pending_posts(host: str, current_user: User, db: Session, current_page: int, per_page: int):
    skip = (current_page - 1) * per_page
    total_posts = db.query(Post).filter(
        Post.USER_CREATE == current_user.USER_ID,
        Post.STATUS == 0
    ).count()
    posts = db.query(Post).filter(
        Post.USER_CREATE == current_user.USER_ID,
        Post.STATUS == 0
    ).order_by(desc(Post.CREATED_AT)).offset(skip).limit(per_page).all()
    all_posts = []
    for post in posts:
        image_path = post.IMAGE.replace("\\", "/")
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        if user:
            post_data = PostOutBase(
                id=post.POST_ID,
                title=post.TITLE,
                image=f"{host}/{image_path}",
                description=post.DESCRIPTION,
                created_at=post.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
                updated_at=post.UPDATE_AT,
                user_create=user.FULL_NAME,
                outstanding=post.OUTSTANDING,
                status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
            )
            all_posts.append(post_data)
    total_page = ceil(total_posts / per_page)
    return PostOutResponse(
        per_page=per_page,
        current_page=current_page,
        total_page=total_page,
        total_post=total_posts,
        posts=all_posts,
    )

# lấy bài viết đang chờ duyệt của admin tổng
def get_pending_posts_for_admin(host: str, current_page: int, per_page: int, db: Session = Depends(get_db)):
    skip = (current_page - 1) * per_page
    total_posts = db.query(Post).filter(
       Post.STATUS == 0
    ).count()
    posts = db.query(Post).filter(
       Post.STATUS == 0
    ).order_by(desc(Post.CREATED_AT)).offset(skip).limit(per_page).all()
    all_posts = []
    for post in posts:
        image_path = post.IMAGE.replace("\\", "/")
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        if user:
            post_data = PostOutBase(
                id=post.POST_ID,
                title=post.TITLE,
                image=f"{host}/{image_path}",
                description=post.DESCRIPTION,
                created_at=post.CREATED_AT,
                updated_at=post.UPDATE_AT,
                user_create=user.FULL_NAME,
                outstanding=post.OUTSTANDING,
                status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
            )
            all_posts.append(post_data)
    total_page = ceil(total_posts / per_page)
    return PostOutResponse(
        per_page=per_page,
        current_page=current_page,
        total_page=total_page,
        total_post=total_posts,
        posts=all_posts,
    )

def get_exception_post(host: str, current_page: int, per_page: int, db: Session ):
    skip = (current_page - 1) * per_page
    total_posts = db.query(Post).filter(
        Post.OUTSTANDING == 1,
        Post.STATUS != -1
    ).count()
    posts = db.query(Post).filter(
        Post.OUTSTANDING == 1,
        Post.STATUS != -1
    ).order_by(desc(Post.CREATED_AT)).offset(skip).limit(per_page).all()
    all_posts = []
    for post in posts:
        image_path = post.IMAGE.replace("\\", "/")
        user = db.query(User).filter(User.USER_ID == post.USER_CREATE).first()
        if user:
            post_data = PostOutBase(
                id=post.POST_ID,
                title=post.TITLE,
                image=f"{host}/{image_path}",
                description=post.DESCRIPTION,
                created_at=post.CREATED_AT,
                updated_at=post.UPDATE_AT,
                user_create=user.FULL_NAME,
                outstanding=post.OUTSTANDING,
                status_name="chờ duyệt" if post.STATUS==0 else "đã duyệt",
                outstanding_name="không nổi bật" if post.OUTSTANDING==0 else "nổi bật"
            )
            all_posts.append(post_data)
    total_page = ceil(total_posts / per_page)
    return PostOutResponse(
        per_page=per_page,
        current_page=current_page,
        total_page=total_page,
        total_post=total_posts,
        posts=all_posts,
    )

# hàm lấy ra danh sách cái bài viết không nổi bật tung.nguyenson11 22/10/2023
def get_post_new(host: str, db: Session):
    try:
        news = db.query(Post).filter(
            Post.OUTSTANDING == 0,
            Post.STATUS == 1
        ).all()
        
        news_data = []
        for new in news:
            image_path = new.IMAGE.replace("\\", "/")
            user = db.query(User).filter(User.USER_ID == new.USER_CREATE).first()
            news_item = News(
                POST_ID=new.POST_ID,
                TITLE=new.TITLE,
                IMAGE=f"{host}/{image_path}",
                USER_CREATE =user.FULL_NAME,
                CREATED_AT =new.CREATED_AT.strftime("%d-%m-%Y %H:%M:%S"),
                # HTML_CONTENT =new.HTML_CONTENT,
                OUTSTANDING =new.OUTSTANDING,
                DESCRIPTION=new.DESCRIPTION,
                UPDATE_AT =new.UPDATE_AT.strftime("%d-%m-%Y %H:%M:%S"),
                STATUS =new.STATUS,
                STATUS_NAME="chờ duyệt" if new.STATUS==0 else "đã duyệt",
                OUTSTANDING_NAME="không nổi bật" if new.OUTSTANDING==0 else "nổi bật"
            )
            news_data.append(news_item)
        
        return news_data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Lỗi hiển thị các bài viết không nổi bật! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")