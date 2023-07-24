from sqlalchemy.orm.session import Session
from db.models import Organization
from fastapi import HTTPException, status 
import re

def get_all_orgs(db:Session):
    org_big= db.query(Organization).filter(Organization.ORG_PARENT_ID.is_(None)).all()
    return org_big
def get_org_by_parent(db: Session,org_parent_id: str):
    organizations = db.query(Organization).filter(Organization.ORG_PARENT_ID == org_parent_id).all()
    return organizations