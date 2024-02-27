from fastapi import HTTPException
from sqlalchemy.orm.session import Session
from db.models import Slogan
from sqlalchemy import desc, update
from schemas import SloganBase, SloganDisplay
from datetime import datetime
    
#get slogan for homepage
def get_slogan(db: Session):
    slogan = db.query(Slogan.HTML_CONTENT).filter(Slogan.OUTSTANDING == 1).first()
    if slogan:
        slogan_data = SloganBase(
            HTML_CONTENT=slogan.HTML_CONTENT
        )
        return slogan_data
    else:
        return SloganBase(HTML_CONTENT="")

def get_all_slogans(db: Session):
    slogans = (
        db.query(Slogan)
        .all()
    )
    if slogans:
        slogan_data = [
            SloganDisplay(
                ID=slogan.SLOGAN_ID,
                HTML_CONTENT=slogan.HTML_CONTENT,
                OUTSTANDING=slogan.OUTSTANDING
            )
            for slogan in slogans
        ]
        return slogan_data
    else:
        return None
    
def create_slogan(db: Session, html_content: str):
    new_slogan = Slogan(
        HTML_CONTENT=html_content,
        CREATED_AT=datetime.now(),
        OUTSTANDING=0
    )
    db.add(new_slogan)
    db.commit()
    db.refresh(new_slogan)
    return {"status": 200, "detail": "Tạo slogan thành công"}

def update_slogan(db: Session, slogan_id: int, slogan_update: SloganBase):
    slogan = db.query(Slogan).get(slogan_id)
    if slogan:
        slogan.HTML_CONTENT = slogan_update.HTML_CONTENT
        db.commit()
        db.refresh(slogan)
        return {"status": 200, "detail": "Chỉnh sửa thành công"}
    else:
        return None

def delete_slogan(db: Session, slogan_id: int):
    slogan = db.query(Slogan).get(slogan_id)
    if slogan:
        db.delete(slogan)
        db.commit()
        return {"status": 200, "detail": "Xóa slogan thành công"}
    else:
        return False

def set_outstanding_slogan(db: Session, slogan_id: int):
    with db.begin():
        db.execute(update(Slogan).values(OUTSTANDING=0))
        
        slogan = db.query(Slogan).filter(Slogan.SLOGAN_ID == slogan_id).first()
        if slogan:
            slogan.OUTSTANDING = 1
            db.commit()
            return {"status": 200, "detail": "Slogan này sẽ được đưa lên màn hình chính"}
        else:
            return False
        
def search_slogan(db: Session, name: str):
    slogans = (
        db.query(Slogan)
        .filter(Slogan.HTML_CONTENT.ilike(f"%{name}%"))
        .order_by(desc(Slogan.OUTSTANDING))
        .all()
    )
    return [slogan for slogan in slogans]
