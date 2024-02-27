# Nguyen Tuan Minh
# 22/07/2023
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
            districts = db.query(Area).filter(Area.DISTRICT != "", Area.PRECINCT =="", Area.PROVINCE == province, Area.STATUS =="1").all()
            for district in districts:
                results.append({"district_id": district.DISTRICT, "district": district.NAME})
            return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Danh sách quận đang bị lỗi!')

def get_provinces_list(db: Session):
    results = []
    try:
        provinces = db.query(Area).filter(Area.DISTRICT =="", Area.PRECINCT=="", Area.STATUS =="1").all()
        for province in provinces:
            results.append({"province_id": province.PROVINCE, "province": province.NAME})
        return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Danh sách tỉnh đang bị lỗi!')

def get_wards_list(db: Session, province: str, district: str):
    results = []
    try:
        if province is not None and district is not None:
            precincts = db.query(Area).filter(Area.PRECINCT !="", Area.DISTRICT == district, Area.PROVINCE == province, Area.STATUS =="1").all()
            for precinct in precincts:
                results.append({"ward_id": precinct.PRECINCT, "ward": precinct.NAME})
            return results
        else:
            return results
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Danh sách phường đang bị lỗi!')

def get_area(user: UserBase, db: Session):
    try:
        area = db.query(Area).filter(Area.PROVINCE == user.province,Area.DISTRICT == user.district, Area.PRECINCT == user.ward ).first()
        if not area:
            return None
        return area.AREA_ID
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi hiển thị vùng theo tỉnh quận huyện! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")


        