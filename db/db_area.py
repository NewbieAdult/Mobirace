from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Area
from schemas import UserBase

def get_districts_list(db: Session, province: str):
    results = []
    try:
        if province is None:
            return results
        else:
            districts = db.query(Area).filter(Area.DISTRICT != "" and Area.PRECINCT =="" and Area.PROVINCE == province and Area.STATUS ==1).all()
            for district in districts:
                results.append({"district_id": district.DISTRICT, "district": district.NAME})
            return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.')

def get_provinces_list(db: Session):
    results = []
    try:
        provinces = db.query(Area).filter(Area.DISTRICT =="" and Area.PRECINCT=="" and Area.STATUS ==1).all()
        for province in provinces:
            results.append({"province_id": province.PROVINCE, "province": province.NAME})
        return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.')



def get_wards_list(db: Session, province: str, district: str):
    results = []
    try:
        if province is None: 
            return results
        elif province is not None and district is not None:
            precincts = db.query(Area).filter(Area.PRECINCT !="" and Area.DISTRICT == district and Area.PROVINCE == province and Area.STATUS ==1).all()
            for precinct in precincts:
                results.append({"ward_id": precinct.PRECINCT, "ward": precinct.NAME})
            return results
        elif district is None:
            precincts = db.query(Area).filter(Area.PRECINCT =="" and Area.PROVINCE == province and Area.STATUS ==1).all()
            for precinct in precincts:
                results.append({"ward_id": precinct.PRECINCT, "ward": precinct.NAME})
            return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail.')

def get_area(user: UserBase, db: Session):
    area = db.query(Area).filter(Area.PROVINCE == user.province,Area.DISTRICT == user.district, Area.PRECINCT == user.ward ).first()
    if not area:
        return None
    return area.AREA_ID


        