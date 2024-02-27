from sqlalchemy import Column, CheckConstraint, Enum, Table
from sqlalchemy.sql.sqltypes import Integer, String,DateTime,Float, Date, Double
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship 
from sqlalchemy.dialects.mysql import LONGTEXT
from db.database import Base
from datetime import datetime

class User(Base):
    __tablename__='USER'
    USER_ID= Column(Integer, primary_key=True)
    USER_NAME= Column(String(100)) 
    PASSWORD= Column(String(500)) 
    EMAIL= Column(String(100))
    # CREATED_AT= Column(DateTime, default= datetime.now()) 
    CREATED_AT= Column(DateTime) 
    FULL_NAME= Column(String(100)) 
    AVATAR_PATH= Column(String(500), nullable = True) 
    DATE_OF_BIRTH=  Column(Date) 
    GENDER= Column(String(50), nullable = True) 
    TEL_NUM= Column(String(15)) 
    TOTAL_DISTANCE= Column(Double, default= 0) 
    RANKING= Column(Integer) 
    PACE = Column(Double, default= 0) 
    STATUS = Column(String(5), server_default='1')
    LINK_FB=Column(String(500)) 
    HOME_NUMBER= Column(String(500)) 
    AREA_ID= Column(Integer, ForeignKey('AREA.AREA_ID'))
    SIZE_ID = Column(Integer, ForeignKey('SHIRT_SIZE.SIZE_ID'),nullable = True)
    ORG_ID= Column(Integer, ForeignKey('ORGANIZATION.ORG_ID'))
    ORG_CHILD_ID= Column(Integer, ForeignKey('ORGANIZATION_CHILD.CHILD_ID'))
    TYPE_ACCOUNT= Column(String(10))
    STRAVA_ID= Column(Integer) 
    STRAVA_ACCESS_TOKEN=Column(String(200))
    STRAVA_REFRESH_TOKEN=Column(String(200))
    STRAVA_FULL_NAME =Column(String(100))
    STRAVA_IMAGE =Column(String(200))
    SYNC_STATUS =Column(String(100))
    clubs = relationship("Club", back_populates="admin_user")
    area = relationship('Area', back_populates='users')

class Role(Base):
    __tablename__='ROLE'
    ROLE_ID=  Column(Integer, primary_key=True)
    ROLE_NAME= Column(String(50)) 
    STATUS= Column(String(50)) 
    CREATED_AT= Column(DateTime) 
  
class User_Role(Base):
    __tablename__='USER_ROLE'
    ROLE_ID=  Column(Integer, primary_key=True)
    USER_ID=  Column(Integer, primary_key=True)

class Role_Function(Base) :
    __tablename__='ROLE_FUNCTION'
    ROLE_ID=  Column(Integer, primary_key=True)
    FUNC_ID= Column(Integer)

class Function(Base):
    __tablename__='FUNCTION'
    FUNC_ID= Column(Integer, primary_key=True)
    USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    FUNC_PARENT_ID= Column(Integer, ForeignKey('FUNCTION.FUNC_ID'))
    FUNC_NAME= Column(String(50)) 
    STATUS= Column(String(50))  
    API_PATH= Column(String(500)) 
    CREATED_AT= Column(DateTime) 
    ICON= Column(String(100))  

class Run(Base):
    __tablename__='RUN'
    RUN_ID= Column(Integer, primary_key=True)
    USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    STRAVA_RUN_ID= Column(Integer)
    NAME= Column(String(500)) 
    DISTANCE= Column(Float)
    DURATION= Column(String(50))
    PACE= Column(Float)
    CALORI= Column(Float)
    CREATED_AT= Column(DateTime) 
    STATUS=Column(String(500)) 
    TYPE= Column(String(500)) 
    HEART_RATE= Column(Double)
    STEP_RATE=Column(Double)
    SUMMARY_POLYLINE=Column(String(1000))
    REASON=Column(String(1000), nullable=True)

class Club(Base):
    __tablename__='CLUB'
    CLUB_ID= Column(Integer, primary_key=True)
    CLUB_NAME= Column(String(100)) 
    DESCRIPTION= Column(String(200)) 
    CREATE_AT= Column(DateTime, default= datetime.now()) 
    CLUB_TOTAL_DISTANCE= Column(Double) 
    CLUB_RANKING= Column(Integer) 
    STATUS= Column(Integer)  
    ADMIN = Column(Integer, ForeignKey('USER.USER_ID'))
    MIN_PACE= Column(Double) 
    MAX_PACE= Column(Double, CheckConstraint('MAX_PACE < MIN_PACE')) 
    PICTURE_PATH= Column(String(200), nullable=True)
    CREATOR_ID=Column(Integer)
    admin_user = relationship("User", back_populates="clubs")
class SYSTEM(Base):
    __tablename__='SYSTEM'
    KEY= Column(String(200), primary_key=True)
    VALUE= Column(Integer) 

User_Club = Table(
    'USER_CLUB',
    Base.metadata,
    # Column("USER_ID", Integer, ForeignKey('USER.USER_ID'), primary_key=True),
    # Column("CLUB_ID", Integer, ForeignKey('CLUB.CLUB_ID'), primary_key=True),
    Column("USER_ID", Integer, primary_key=True),
    Column("CLUB_ID", Integer, primary_key=True),
    Column("JOIN_DATE", DateTime),
    Column("TOTAL_DISTANCE", Double),
    Column("RANKING", Integer),
    Column("PACE", Double)
)

Club_Event = Table(
    'CLUB_EVENT',
    Base.metadata,
    Column("CLUB_ID", Integer, ForeignKey('CLUB.CLUB_ID'), primary_key=True),
    Column("EVENT_ID", Integer, ForeignKey('EVENT.EVENT_ID'), primary_key=True),
    Column("JOIN_DATE", DateTime),
    Column("TOTAL_DISTANCE", Double),
    Column("RANKING", Integer),
    Column("PACE", Double)
)

class Event(Base):
    __tablename__='EVENT'
    EVENT_ID= Column(Integer, primary_key=True)
    DESCRIPTION= Column(String(100)) 
    TITLE= Column(String(100)) 
    CREATE_AT= Column(DateTime)
    PICTURE_PATH= Column(String(200), nullable= True) 
    START_DATE= Column(DateTime)
    END_DATE= Column(DateTime)
    STATUS= Column(Integer) 
    RUNNING_CATEGORY= Column(String(100)) 
    NUM_OF_ATTENDEE=Column(Integer)
    NUM_OF_RUNNER= Column(Integer)
    TOTAL_DISTANCE= Column(Double)
    CONTENT= Column(LONGTEXT)
    MIN_PACE= Column(Double) 
    MAX_PACE= Column(Double, CheckConstraint('MAX_PACE > MIN_PACE'))
    OUTSTANDING=Column(Integer)
    USER_CREATE=Column(Integer, ForeignKey('USER.USER_ID'))
    ADMIN = Column(Integer, ForeignKey('USER.USER_ID'))
    user = relationship("User", foreign_keys=[USER_CREATE]) 

class UserEvent(Base): 
    __tablename__='USER_EVENT'
    USER_ID=  Column(Integer, primary_key=True)
    EVENT_ID=  Column(Integer, primary_key=True)
    JOIN_DATE=Column(DateTime)
    TOTAL_DISTANCE= Column(Double)
    RANKING=Column(Integer)
    PACE= Column(Double)
    
class Organization(Base):
    __tablename__ = "ORGANIZATION"
    ORG_ID = Column(Integer, primary_key=True, index=True)
    ORG_NAME = Column(String(100), nullable=False)
    ORG_PARENT_ID = Column(Integer, ForeignKey("ORGANIZATION.ORG_ID"))

    children = relationship("Organization", back_populates="parent", remote_side=[ORG_ID])
    parent = relationship("Organization", back_populates="children", remote_side=[ORG_PARENT_ID])
  
class Post(Base):
    __tablename__='POST'
    POST_ID= Column(Integer, primary_key=True)
    TITLE=Column(LONGTEXT) 
    IMAGE=Column(String(200)) 
    USER_CREATE = Column(Integer, ForeignKey('USER.USER_ID'))
    CREATED_AT= Column(DateTime)
    HTML_CONTENT=Column(LONGTEXT)
    # OUTSTANDING=Column(Integer, CheckConstraint('OUTSTANDING IN (-1, 0, 1)'), default=-1)
    OUTSTANDING=Column(Integer, default=0)
    DESCRIPTION=Column(LONGTEXT)
    UPDATE_AT=Column(DateTime)
    # STATUS =Column(Integer, CheckConstraint('OUTSTANDING IN (0, 1)'), default=0)
    STATUS =Column(Integer, default=0)
    user = relationship("User", foreign_keys=[USER_CREATE])
    OUTSTANDING_AT= Column(DateTime)

class Shirt_Size(Base):
    __tablename__='SHIRT_SIZE'
    SIZE_ID= Column(Integer, primary_key=True)
    SIZE_NAME= Column(String(100))
  
class Area(Base):
    __tablename__='AREA'
    AREA_ID= Column(Integer, primary_key=True)
    PROVINCE= Column(String(50)) 
    DISTRICT=Column(String(100)) 
    PRECINCT= Column(String(100)) 
    NAME= Column(String(100)) 
    FULL_NAME= Column(String(100)) 
    STATUS= Column(String(10)) 
    users = relationship('User', back_populates='area')

class Slogan(Base):
    __tablename__='SLOGAN'
    SLOGAN_ID= Column(Integer, primary_key=True)
    HTML_CONTENT= Column(String(500)) 
    CREATED_AT= Column(DateTime)
    OUTSTANDING=Column(Integer, CheckConstraint('OUTSTANDING IN (0, 1)'), default=0)

class Organization_Child(Base):
    __tablename__="ORGANIZATION_CHILD"
    CHILD_ID=Column(Integer,primary_key=True,index=True)
    CHILD_NAME=Column(String(100))
    ORG_ID=Column(Integer,ForeignKey("ORGANIZATION.ORG_ID"))
    # organization = relationship("Organization", back_populates="children")

class Log_Post(Base):
    __tablename__ = 'LOG_POST'
    LOG_ID = Column(Integer, primary_key=True)
    POST_ID = Column(Integer)
    ACTION = Column(Enum('delete', 'modify'), nullable=False)
    TITLE_BEFORE= Column(LONGTEXT)
    DESCRIPTION_BEFORE=Column(LONGTEXT)
    CONTENT_BEFORE = Column(LONGTEXT)
    IMAGE_BEFORE = Column(LONGTEXT)
    TITLE_AFTER = Column(LONGTEXT)
    DESCRIPTION_AFTER=Column(LONGTEXT)
    CONTENT_AFTER = Column(LONGTEXT)
    IMAGE_AFTER = Column(LONGTEXT)
    USER_MODIFY = Column(Integer)
    CREATED_AT = Column(DateTime, default=datetime.now())
    
class User_Event_Activity(Base):
    __tablename__='USER_EVENT_ACTIVITY'
    ID=Column(Integer,primary_key=True, autoincrement=True)
    RUN_ID= Column(Integer)
    USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    NAME= Column(String(500)) 
    DISTANCE= Column(Float)
    DURATION= Column(String(50))
    PACE= Column(Float)
    CALORI= Column(Float)
    CREATED_AT= Column(DateTime) 
    STATUS=Column(String(500))  
    EVENT_ID = Column(Integer, ForeignKey('USER_EVENT.EVENT_ID'))
    REASON=Column(String(500))
    
class User_Club_Activity(Base):
    __tablename__='USER_CLUB_ACTIVITY'
    ID=Column(Integer,primary_key=True, autoincrement=True)
    RUN_ID= Column(Integer)
    # USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    USER_ID= Column(Integer)
    NAME= Column(String(500)) 
    DISTANCE= Column(Float)
    DURATION= Column(String(50))
    PACE= Column(Float)
    CALORI= Column(Float)
    CREATED_AT= Column(DateTime) 
    STATUS=Column(String(500))  
    # CLUB_ID = Column(Integer, ForeignKey('USER_CLUB.CLUB_ID'))
    CLUB_ID = Column(Integer)
    REASON=Column(String(500))

# tung.nguyenson11 ghi log webhook 10/10/2023
class Webhook_Log(Base):
    __tablename__='WEBHOOK_LOG'
    LOG_ID=Column(Integer,primary_key=True, autoincrement=True)
    HUB_VERIFY_TOKEN= Column(String(500))
    HUB_CHALLENGE= Column(String(500))
    HUB_MODE= Column(String(500)) 
    CREATED_AT= Column(DateTime)
#can.lt 14/10/23
class Flaudulent_Activity_Club(Base):
    __tablename__='FRAUDULENT_ACTIVITY_CLUB'
    CLUB_ID=Column(Integer,primary_key=True)
    ACTIVITY_ID=Column(Integer,primary_key=True)
    CREATED_ID=Column(Integer)
    CREATE_DATETIME= Column(DateTime)
    REASON=Column(String(500))

#can.lt 14/10/23
class Flaudulent_Activity_Event(Base):
    __tablename__='FRAUDULENT_ACTIVITY_EVENT'
    EVENT_ID=Column(Integer,primary_key=True)
    ACTIVITY_ID=Column(Integer,primary_key=True)
    CREATED_ID=Column(Integer)
    CREATE_DATETIME= Column(DateTime)
    REASON=Column(String(500))

#can.lt 14/10/23
# class User_Club(Base):
#     __tablename__='USER_CLUB'
#     USER_ID=Column(Integer,primary_key=True)
#     CLUB_ID=Column(Integer,primary_key=True)
#     TOTAL_DISTANCE=Column(Double)
#     JOIN_DATE= Column(DateTime)
#     RANKING=Column(Integer)
#     PACE=Column(Integer)

# tung.nguyenson11 ghi log webhook 16/10/2023
class Webhook_Log_1(Base):
    __tablename__='WEBHOOK_LOG_1'
    LOG_ID=Column(Integer,primary_key=True, autoincrement=True)
    ASPECT_TYPE= Column(String(100))
    EVENT_TIME= Column(Integer)
    OBJECT_ID= Column(Integer)
    OBJECT_TYPE= Column(String(100))
    OWNER_ID= Column(Integer)
    SUBSCRIPTION_ID= Column(Integer)
    CREATED_AT= Column(DateTime) 