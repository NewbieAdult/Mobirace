from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import db_org
from db.database import SessionLocal
from db.models import Organization
router=APIRouter(
    prefix='/organization',
    tags=['organization']
)

@router.get("/")
def get_organizations():
    try:
        db = SessionLocal()
        # Lấy cả tổng công ty và công ty
        organizations = db.query(Organization).all()

        if not organizations:
            raise HTTPException(status_code=404, detail="No organizations found.")

        # Lấy danh sách tổng công ty (những organization có ORG_PARENT_ID là None)
        root_organizations = [org for org in organizations if org.ORG_PARENT_ID is None]

        # Xây dựng danh sách cây từ tổng công ty và các công ty con
        tree = []
        for org in root_organizations:
            tree.append(db_org.get_sub_organizations(org, organizations))

        return tree

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hiển thị danh sách tổ chức! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

    finally:
        db.close()
@router.get("/child/")
def get_organization_child(org_id: int,db:Session=Depends(get_db)):
    return db_org.get_org_by_parent(db,org_id)