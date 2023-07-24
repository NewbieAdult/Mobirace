from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String,DateTime,Float,Double, Date
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Table
from sqlalchemy.dialects.mysql import LONGTEXT
from db.database import Base
from datetime import datetime

class User(Base):
    __tablename__='USER'
    USER_ID= Column(Integer, primary_key=True)
    USER_NAME= Column(String(100)) 
    PASSWORD= Column(String(500)) 
    EMAIL= Column(String(100))
    CREATED_AT= Column(DateTime, default=datetime.now()) 
    FULL_NAME= Column(String(100)) 
    AVATAR_PATH= Column(String(500)) 
    DATE_OF_BIRTH=  Column(Date) 
    GENDER= Column(String(50)) 
    TEL_NUM= Column(String(15)) 
    TOTAL_DISTANCE= Column(Double) 
    RANKING= Column(Integer) 
    STATUS = Column(String(5), server_default='1')
    LINK_FB=Column(String(500)) 
    HOME_NUMBER= Column(String(500)) 
    AREA_ID= Column(Integer, ForeignKey('AREA.AREA_ID'))
    SIZE_ID = Column(Integer, ForeignKey('SHIRT_SIZE.SIZE_ID'))
    ORG_ID= Column(String(50), ForeignKey('ORGANIZATION.ORG_ID'))
    sizes = relationship("Shirt_Size", back_populates="users")  
    roles = relationship("Role", secondary='USER_ROLE',back_populates="users")
    functions = relationship("Function", back_populates="users")
    runs = relationship("Run", back_populates="users")
    organizations = relationship("Organization", back_populates="users")
    clubs = relationship("Club", secondary='USER_CLUB', back_populates="users")
    events = relationship("Event", secondary='USER_EVENT', back_populates="users")
    posts = relationship("Post", back_populates="users")
    areas = relationship("Area", back_populates="users") 

class Role(Base):
    __tablename__='ROLE'
    ROLE_ID=  Column(Integer, primary_key=True)
    ROLE_NAME= Column(String(50)) 
    STATUS= Column(String(50)) 
    CREATED_AT= Column(DateTime) 
    users = relationship("User", secondary='USER_ROLE',back_populates="roles")
    functions = relationship("Function", secondary='ROLE_FUNCTION', back_populates="roles")

User_Role = Table(
    'USER_ROLE',
    Base.metadata,
    Column('USER_ID', Integer, ForeignKey('USER.USER_ID'), primary_key=True),
    Column('ROLE_ID', Integer, ForeignKey('ROLE.ROLE_ID'), primary_key=True)
) 

class Function(Base):
    __tablename__='FUNCTION'
    FUNC_ID= Column(Integer, primary_key=True)
    USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    FUNC_PARENT_ID= Column(Integer, ForeignKey('FUNCTION.FUNC_ID'))
    FUNC_NAME= Column(String(50)) 
    STATUS= Column(String(50))  
    API_PATH= Column(String(500)) 
    CREATED_AT= Column(DateTime) 
    roles = relationship("Role", secondary='ROLE_FUNCTION', back_populates="functions")
    users = relationship("User", back_populates="functions")
    func_children = relationship("Function", backref="func_parent", remote_side=[FUNC_ID])

Role_Function = Table(
    'ROLE_FUNCTION',
    Base.metadata,
    Column("FUNC_ID", Integer, ForeignKey('ROLE.ROLE_ID'), primary_key=True),
    Column("ROLE_ID", Integer, ForeignKey('FUNCTION.FUNC_ID'), primary_key=True)
)

class Run(Base):
    __tablename__='RUN'
    RUN_ID= Column(Integer, primary_key=True)
    USER_ID= Column(Integer, ForeignKey('USER.USER_ID'))
    STRAVA_ID= Column(Integer)
    NAME= Column(String(50)) 
    DISTANCE= Column(Float)
    DURATION= Column(Float)
    PACE= Column(Float)
    CALORI= Column(Float)
    CREATED_AT= Column(DateTime) 
    STATUS=Column(String(50)) 
    TYPE= Column(String(50)) 
    HEART_RATE= Column(Double)
    STEP_RATE=Column(Double)
    users = relationship("User", back_populates="runs")

class Club(Base):
    __tablename__='CLUB'
    CLUB_ID= Column(Integer, primary_key=True)
    CLUB_NAME= Column(String(100)) 
    DESCRIPTION= Column(String(200)) 
    CREATE_AT= Column(DateTime) 
    CLUB_TOTAL_DISTANCE= Column(Double) 
    CLUB_RANKING= Column(Integer) 
    STATUS= Column(Integer)  
    ADMIN= Column(Integer) 
    MIN_PACE= Column(Double) 
    MAX_PACE= Column(Double) 
    PICTUTE_PATH= Column(String(500)) 
    users = relationship("User", secondary='USER_CLUB', back_populates="clubs")
    events = relationship("Event", secondary='CLUB_EVENT', back_populates="clubs")

User_Club = Table(
    'USER_CLUB',
    Base.metadata,
    Column("USER_ID", Integer, ForeignKey('USER.USER_ID'), primary_key=True),
    Column("CLUB_ID", Integer, ForeignKey('CLUB.CLUB_ID'), primary_key=True),
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
    PICTURE_PATH= Column(String(500)) 
    START_DATE= Column(DateTime)
    END_DATE= Column(DateTime)
    STATUS= Column(String(100)) 
    RUNNING_CATEGORY= Column(String(100)) 
    NUM_OF_ATTENDEE=Column(Integer)
    NUM_OF_RUNNER= Column(Integer)
    TOTAL_DISTANCE= Column(Double)
    CONTENT= Column(LONGTEXT)
    MAX_PACE=Column(Double)
    users = relationship("User", secondary='USER_EVENT', back_populates="events")
    clubs = relationship("Club", secondary='CLUB_EVENT', back_populates="events")

UserEvent = Table(
    'USER_EVENT',
    Base.metadata,
    Column("USER_ID", Integer, ForeignKey('USER.USER_ID'),primary_key=True),
    Column("EVENT_ID", Integer, ForeignKey('EVENT.EVENT_ID'), primary_key=True),
    Column("JOIN_DATE", DateTime),
    Column("TOTAL_DISTANCE", Double),
    Column("RANKING", Integer),
    Column("PACE", Double)
)

class Organization(Base):
    __tablename__ = 'ORGANIZATION'
    ORG_ID = Column(String(50), primary_key=True)
    ORG_NAME = Column(String(100))   
    ORG_PARENT_ID = Column(String(100), ForeignKey('ORGANIZATION.ORG_ID'))   
    org_children = relationship("Organization", backref="org_parent", remote_side=[ORG_ID])
    users=relationship("User",back_populates="organizations")

class Post(Base):
    __tablename__='POST'
    POST_ID= Column(Integer, primary_key=True)
    TITLE=Column(String(100)) 
    USER_ID = Column(Integer, ForeignKey('USER.USER_ID'))
    CREATED_AT= Column(DateTime)
    HTML_CONTENT=Column(LONGTEXT)
    users = relationship("User", back_populates="posts")

class Shirt_Size(Base):
    __tablename__='SHIRT_SIZE'
    SIZE_ID= Column(Integer, primary_key=True)
    SIZE_NAME= Column(String(100))
    users = relationship("User", back_populates="sizes") 

class Area(Base):
    __tablename__='AREA'
    AREA_ID= Column(Integer, primary_key=True)
    PROVINCE= Column(String(50)) 
    DISTRICT=Column(String(100)) 
    PRECINCT= Column(String(100)) 
    NAME= Column(String(100)) 
    FULL_NAME= Column(String(100)) 
    STATUS= Column(String(10)) 
    users = relationship("User", back_populates="areas") 