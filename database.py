from sqlalchemy import create_engine, Integer, Column, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker,DeclarativeBase

engine = create_engine('sqlite:///database.db', echo=True)

def get_db():
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    return db

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    login = Column(String, primary_key=True)
    password = Column(String)
    access_token = Column(String,default=None)
    logged_in = Column(Boolean,default=False)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True,autoincrement=True)
    name = Column(String)
    description = Column(String)
    status = Column(Boolean)
    user = Column(String, ForeignKey('users.login'))


Base.metadata.create_all(engine)
