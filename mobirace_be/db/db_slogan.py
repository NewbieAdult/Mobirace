from fastapi import HTTPException, status
from sqlalchemy.orm.session import Session
from db.models import Post
from sqlalchemy import desc

#get slogan
def get_slogan(db: Session, num_events : int = 3):
  return db.query(Post).order_by(desc(Post.CREATED_AT)).limit(num_events).all()


