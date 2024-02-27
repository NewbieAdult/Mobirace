from sqlalchemy.orm.session import Session
from db.models import Organization_Child

import re
from db.database import SessionLocal
def get_sub_organizations(org, organizations):
    org_list = []
    org_dict = {
        "ORG_ID": org.ORG_ID,
        "ORG_NAME": org.ORG_NAME,
        "ORG_PARENT_ID":org.ORG_PARENT_ID,
        "children": org_list
    }
    for child in organizations:
        if child.ORG_PARENT_ID == org.ORG_ID:
            org_list.append(get_sub_organizations(child, organizations))
    return org_dict

def get_org_by_parent(db: Session,org_id: int):
    organizations = db.query(Organization_Child).filter(Organization_Child.ORG_ID == org_id).all()
    return organizations if organizations else []
