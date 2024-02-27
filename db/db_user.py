#25/7/2023
#Nguyen Sinh Hung
# thien.tranthi add host: str = Depends(get_base_url) 08/09/2023
from sqlalchemy.orm.session import Session
from schemas import UserBase, User_Change_Password, User_Reset_Password
from db.models import User, Run, Area
from fastapi import HTTPException, status, Form, UploadFile
from db.db_area import get_area
from db.db_run import get_all_activities, add_all_activities
from email.message import EmailMessage
from utils.generate_password import random_password, generate_password
from utils.hash import Hash
from utils.recaptcha import verify_recaptcha
from utils.strava import exchange_authorization_code
from datetime import datetime
from jobs.tasks import *
from math import ceil
from fastapi.responses import JSONResponse
import os, shutil, ssl, smtplib
from typing import Optional, Union
from lib.send_email import send_email


host_fe = os.getenv("host_fe")

#create user
async def create_user(request: UserBase, db: Session):
    user = get_user_by_username(request.username,db)
    email = get_user_by_email_and_typeaccount(request.email,request.type_account,db)
    recaptcha_token = request.recaptcha_token
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Tài khoản đã tồn tại')
    elif email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email đã tồn tại')
    score = 0
    try:
        recaptcha_response = await verify_recaptcha(recaptcha_token)
        score = recaptcha_response["score"]
    except:
        raise HTTPException(status_code=400, detail='Xác thực capcha thất bại!')
    if score < 0.5:
        raise HTTPException(status_code=400, detail="Thao tác khả nghi")
    else:
        try:
            area_id = get_area(request,db)
            new_user = User(
                USER_NAME = request.username,
                PASSWORD = request.password,
                FULL_NAME = request.fullname,
                EMAIL = request.email,
                CREATED_AT = datetime.now(), 
                TEL_NUM = request.telNumber,
                DATE_OF_BIRTH = request.birthday,
                GENDER = request.gender if request.gender and request.gender != '' else None,
                HOME_NUMBER = request.address,
                SIZE_ID = request.size_id,
                LINK_FB = request.link_fb,
                ORG_ID = request.org_id,
                ORG_CHILD_ID = request.child_org_id,
                AREA_ID = area_id,
                TYPE_ACCOUNT = request.type_account,
                TOTAL_DISTANCE= 0,
                PACE= 0
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            update_user_ranking(db)

            response = {
                "status": 200,
                "detail": "Thao tác thành công!"
            }
            return response
        except:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Thao tác thất bại!')

def change_password(user: User_Change_Password, db: Session, current_user: User):
    try:
        authenticate_user(current_user,user.old_password)
        current_user.PASSWORD = Hash.bcrypt(user.new_password)
        db.commit()
        response = {
            "status": 200,
            "detail": "Đổi mật khẩu thành công"
        }
        return response
    except :
        db.rollback()
        raise HTTPException(status_code=401, detail="Mật khẩu cũ không đúng")

def authenticate_user(user: User, password: str):
    if not Hash.verify(user.PASSWORD, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu cũ không đúng",
        )
    
def get_user_by_username(username: str, db: Session):
    try: 
        user = db.query(User).filter(User.USER_NAME == username).first()
        if not user:
            return None
        return user
    except :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail')

def get_user_by_email(email: str, db: Session): 
    user = db.query(User).filter(User.EMAIL == email).first()
    if not user:
        return None
    return user

def get_user_by_email_and_typeaccount(email: str, type_account: str, db: Session):
    user = db.query(User).filter(User.EMAIL == email, User.TYPE_ACCOUNT == type_account).first()
    if not user:
        return None
    return user

def get_user_by_username_and_typeaccount(user_name: str, type_account: str, db: Session):
    user = db.query(User).filter(User.USER_NAME == user_name, User.TYPE_ACCOUNT == type_account).first()
    if not user:
        return None
    return user

def get_user_by_stravaId(strava_id: int, db: Session):
    user = db.query(User).filter(User.STRAVA_ID == strava_id).first()
    if not user:
        return None
    return user

def reset_password(request: User_Reset_Password, db: Session):
    user = get_user_by_username(request.username,db)
    email = get_user_by_email(request.email,db)
    if user and email:
        email_sender = 'hung66522@gmail.com'
        email_password = 'nqgcxptiaomdicyr'
        # email_sender = 'giaiphapdoanhnghiep@mobifone.vn'
        # email_password = 'Abc@12345'
        # smtp_server = 'email.mobifone.vn'
        # port = 25
        email_receiver = f'{request.email}'
        new_password = random_password()
        hash_password = Hash.bcrypt(new_password)
        subject = 'Password Reset Request'
        body = f"""
        New password: {new_password}
        """

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)
    
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            # with smtplib.SMTP_SSL(smtp_server, 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.send_message(em)
            try:
                user.PASSWORD = hash_password
                db.commit()
            except: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Execution fail')


        except smtplib.SMTPAuthenticationError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to authenticate with the SMTP server.')
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to send the reset password email.')


        response = {
            "status": 200,
            "detail": "Reset mật khẩu thành công"
        }
        return response
        
    else: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='username và email không đúng')

#NGUYEN SINH HUNG 27/7/2023 
#update user     
def update_user(db: Session, current_user: User,
                fullname: str =Form(None), 
                email: Optional[str] =Form(None) ,
                telNumber: Optional[str] =Form(None),
                birthday: datetime=Form(None),
                gender: Optional[str] =Form(None),
                address: Optional[str]=Form(None),
                province: Optional[str]=Form(None),
                district: Optional[str]=Form(None),
                ward: Optional[str]=Form(None),
                org_id:  Union[int, str] =Form(None),
                child_org_id:  Union[int, str] =Form(None),
                size_id: Union[int, str] =Form(None),
                link_fb: Optional[str]=Form(None),
                image: Union[UploadFile,str] = Form(None)):
    try:
        # area_id = get_area(request, db)
        area = db.query(Area).filter(Area.PROVINCE == province,Area.DISTRICT == district, Area.PRECINCT == ward ).first()
        area_id = area.AREA_ID if area else None
        user = db.query(User).filter(User.USER_NAME == current_user.USER_NAME).first()
        old_image_path = user.AVATAR_PATH
        if image != 'null':           
            formatted_date = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename= f"user_add_{formatted_date}.jpg"

            with open(os.path.join("images", filename), "wb") as f:
                shutil.copyfileobj(image.file, f) 

            image_path = os.path.join('images', filename)
            updated_data = {
                "FULL_NAME": fullname,
                "TEL_NUM": telNumber,
                "DATE_OF_BIRTH": birthday,
                "GENDER": gender if gender and gender != 'null' else None,
                "HOME_NUMBER": address if address != 'null' else None,
                "SIZE_ID": size_id if size_id != 'null' else None,            
                "ORG_ID": org_id if org_id != 'null' else None,
                'ORG_CHILD_ID' : child_org_id if child_org_id != 'null' else None,
                "LINK_FB": link_fb if link_fb != 'null' else None,
                'AVATAR_PATH': image_path,
                "AREA_ID": area_id
            }
            if current_user.TYPE_ACCOUNT==None:
                updated_data["EMAIL"] = email

            if old_image_path != 'images\\no_avatar_strava.png' and (old_image_path and  os.path.exists(old_image_path)):
                old_image_filename = os.path.basename(old_image_path)
                if old_image_filename:
                        os.remove(old_image_path)

            db.query(User).filter(User.USER_NAME == current_user.USER_NAME).update(updated_data)
            db.commit()
            update_user_ranking(db) 
        else:
            updated_data = {
                "FULL_NAME": fullname,
                "TEL_NUM": telNumber,
                "DATE_OF_BIRTH": birthday,
                "GENDER": gender if gender and gender != 'null' else None,
                "HOME_NUMBER": address if address != 'null' else None,
                "SIZE_ID": size_id if size_id != 'null' else None,            
                "ORG_ID": org_id if org_id != 'null' else None,
                'ORG_CHILD_ID' : child_org_id if child_org_id != 'null' else None,
                "LINK_FB": link_fb if link_fb != 'null' else None,
                'AVATAR_PATH': current_user.AVATAR_PATH,
                "AREA_ID": area_id
            }
            if current_user.TYPE_ACCOUNT==None:
                updated_data["EMAIL"] = email
            # Sử dụng Semaphore để đồng bộ hóa
            db.query(User).filter(User.USER_NAME == current_user.USER_NAME).update(updated_data)
            db.commit()
            update_user_ranking(db) 

        response = {
            "status": 200,
            "detail": "Thao tác thông tin thành công!"
        }
        return response
    except :
        db.rollback()
        raise HTTPException(status_code=500, detail="Quá trình cập nhật người dùng bị lỗi! Liên lạc quản trị hệ thống để hỗ trợ!")
#Sinh Hung 4/8/2023
def add_info_strava(code: str, db: Session, current_user: User):
    try:
        strava_info = exchange_authorization_code(code)
        if get_user_by_stravaId(strava_info['athlete']['id'], db):
            raise HTTPException(status_code=409, detail='strava_id đã tồn tại') 
        after = int(current_user.CREATED_AT.timestamp())
        user_activities = get_all_activities(strava_info['access_token'], after)
        add_all_activities(user_activities, db, current_user)
        current_user.STRAVA_ID = strava_info['athlete']['id']
        current_user.STRAVA_ACCESS_TOKEN = strava_info['access_token']
        current_user.STRAVA_REFRESH_TOKEN = strava_info['refresh_token']
        current_user.STRAVA_FULL_NAME = strava_info['athlete']['firstname'] + ' ' + strava_info['athlete']['lastname']
        current_user.STRAVA_IMAGE = strava_info['athlete']['profile']
        current_user.PACE = db.query(func.avg(Run.PACE)).filter(Run.USER_ID == current_user.USER_ID).scalar() or 0
        current_user.TOTAL_DISTANCE = db.query(func.sum(Run.DISTANCE)).filter(Run.USER_ID == current_user.USER_ID).scalar() or 0
        db.commit()

        response = {
            "message": "Kết nối thành công",
            "strava_userid": current_user.STRAVA_ID,
            "strava_fullname": current_user.STRAVA_FULL_NAME,
            "strava_image": current_user.STRAVA_IMAGE
        }
        sync_runs_to_user_event_activity(db)
        sync_runs_to_user_club_activity(db)

        update_ranking_user_event(db)
        update_user_club_distance_and_pace(db)
        update_user_club_ranking(db)
        calculate_club_total_distance(db)
        update_club_ranking(db)
        # update_user_ranking(db)
        update_ranking_event(db)
        
        print(response)
        return response
    except Exception as e:
        db.rollback()
        response = {
            "message": "Kết nối thất bại"
            }
        return JSONResponse(content=response, status_code=500)
    
def search_user(host: str, text_search : str,per_page : int, current_page : int, db: Session):
    try:
        skip = (current_page - 1) * per_page
        users = db.query(User)
        if text_search !=None:
            users=users.filter(User.FULL_NAME.ilike(f"%{text_search}%"))
        total_user = users.count()
        users = users.offset(skip).limit(per_page).all()
        result = []
        for user in users:
            image_path = user.AVATAR_PATH.replace("\\", "/")
            avatar_path = f"{host}/{image_path}"
            status = "Chưa đồng bộ"
            if user.SYNC_STATUS == "-1":
                status = "Đồng bộ thất bại"
            elif user.SYNC_STATUS == "-2":
                status = "Chưa kết nối Strava"
            elif user.SYNC_STATUS == "0":
                status = "Đang đồng bộ"
            elif user.SYNC_STATUS == "1":
                status = "Đã đồng bộ"
            new_user = {
                "user_id": user.USER_ID,
                "user_name": user.FULL_NAME,
                "user_image": avatar_path,
                "user_pace": user.PACE,
                "user_distance": user.TOTAL_DISTANCE,
                "status": status
            }
            result.append(new_user)
        total_page = ceil(int(total_user) / per_page)
        data = {
            "per_page": per_page,
            "current_page": current_page,
            "total_page": total_page,
            "total_user": total_user,
            "users": result
        }
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi tìm kiếm người dùng! Vui lòng liên hệ quản trị hệ thống hỗ trợ!")

def get_info_user_strava(db: Session, current_user: User):
    try:
        status="0"
        if current_user.STRAVA_ID:
            status="1"
        response = {
            "status": status,
            "strava_fullname": current_user.STRAVA_FULL_NAME,
            "strava_image": current_user.STRAVA_IMAGE
        }     
        return response
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        response = {
            "message": "Kết nối thất bại"
            }
        return JSONResponse(content=response, status_code=400)

def reset_password_user(request: User_Reset_Password, db: Session, host: str):
    username = request.username
    email = request.email
    user = db.query(User).filter(User.USER_NAME == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                           detail=f'Tài khoản {username} không tồn tại!')
    try:
        if email == user.EMAIL:
            new_password = generate_password(10)
            content = """ 
IMPORTANT NOTICE:
The information in this email is the property of MobiFone. This communication is confidential and intended solely for the addressee(s). Any unauthorized review, use, disclosure or distribution is prohibited. If you believe this message has been sent to you in error, please notify the sender by replying to this transmission and delete the message without disclosing it. Thank you.
E-mail including attachments is susceptible to data corruption, interception, unauthorized amendment, tampering and viruses, and we only send and receive emails on the basis that we are not liable for any such corruption, interception, amendment, tampering or viruses or any consequences thereof.

THÔNG BÁO BẢO MẬT:
Thông tin trong e-mail này là tài sản của MobiFone. Việc trao đổi thư tín này mang tính chất bảo mật và chỉ dành cho người có tên trong địa chỉ người nhận trên đây. Ngăn cấm bất kỳ việc phê bình, sử dụng, tiết lộ hoặc phân phối trái phép thông tin trao đổi trên đây. Nếu quý vị tin rằng thông tin này gửi tới quý vị do một lỗi nào đó thì xin quý vị hãy thông báo cho người gửi thư bằng cách trả lời thư và xóa thông tin mà quý vị đã nhận được, và không tiết lộ những thông tin này. Trân trọng cám ơn quý vị!
Thư này bao gồm các tập tin đính kèm. Dữ liệu có thể bị sửa đổi, bị chặn và thay đổi trái phép, bị xáo trộn và có thễ bị nhiễm virus. Chúng tôi chỉ gửi và nhận thư trên cơ sở chúng tôi không chịu trách nhiệm trước những việc sửa đổi, việc bị chặn, xáo trộn hay lây nhiễm virus  hay bất kỳ hậu quả nào từ các việc nêu trên.
            """
            
            
            send_email(  email_sender='giaiphapdoanhnghiep@mobifone.vn',
                                email_password='Abc@12345',
                                smtp_server='email.mobifone.vn',
                                smtp_port=25,
                                receivers=[email],
                                # html_template_file_path="templates/email_templates/password_reset.html",
                                html_fillin_dict={"fullname": user.FULL_NAME, 
                                                "username": user.USER_NAME, 
                                                "password": new_password},
                                subject="Reset Password Confirmation",
                                body= f"""
Trang Web giải chạy Mobirun thuộc Trung Tâm Dịch Vụ Công Nghệ Số Công ty MobiFone Khu Vực 2 xin thông báo:
    Đây là mật khẩu cấp mới dành cho tài khoản {user.USER_NAME}
    New password: {new_password}
Link đăng nhập: {host_fe}
                                {content}
                                        """
                                )
            user.PASSWORD = Hash.bcrypt(new_password)
            db.commit()
            return {"detail": 'Mật khẩu mới đã được gửi qua Email!'}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                           detail=f'Tài khoản {username} không được đăng ký bởi {email}! Vui lòng nhập email mà bạn đã đăng ký trên hệ thống!')