from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends
from jwt import InvalidTokenError
from sqlalchemy import insert, update, select, delete
from sqlalchemy.orm import Session
from authentication import create_token, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_TIME, decode_token
from database import User, get_db, Task
from schemes import User as UserSchema, Token, Task as TaskSchema, UpdateTask, PatchTask, DeleteTask

app = FastAPI()

async def get_current_user(token:str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = decode_token(token)
        if not payload:
            raise credentials_exception
        username: str = payload.get("sub")
    except InvalidTokenError:
        raise credentials_exception
    user = db.execute(User.select().where(User.username == username)).fetchone()
    if user is None:
        raise credentials_exception
    if not user.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user

@app.get("/authenticate")
async def authenticate(user:UserSchema,session:Annotated[Session,Depends(get_db)]):
    result = session.execute(select(User).where(User.login==user.login)).fetchone()
    if result.check_password(user.password):
        access_token = create_token("access",{"sub":user.login},ACCESS_TOKEN_EXPIRE_MINUTES)
        session.execute(update(User).values(access_token=access_token,logged_in=True).where(User.login==user.login))
        session.commit()
        refresh_token = create_token("refresh",{"sub":user.login},REFRESH_TOKEN_EXPIRE_TIME)
        return {"access_token":access_token,"refresh_token":refresh_token}
    else:
        raise HTTPException(status_code=401,detail="Invalid credentials")
@app.post("/register")
async def register(user:UserSchema,session:Annotated[Session,Depends(get_db)]):
    access_token = create_token("access", {"sub": user.login}, ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_token("refresh",{"sub": user.login},REFRESH_TOKEN_EXPIRE_TIME)
    result = session.execute(insert(User).values(login=user.login,
                                                 password=user.password,
                                                 access_token=access_token,
                                                 logged_in= True
                                                 ))
    return {"status":"Register is complete","access_token":access_token,"refresh_token":refresh_token}

@app.post("/refresh")
async def refresh(token:Token,session:Annotated[Session,Depends(get_db)]):
    if token.type!="refresh":
        raise HTTPException(status_code=401,detail="Invalid token")
    else:
        refresh_token = decode_token(token.token)
        if not token:
            raise HTTPException(status_code=401,detail="Invalid token")
        if datetime.now(timezone.utc)>refresh_token.expire:
            raise HTTPException(status_code=401,detail="Token expired")
        else:
            login = refresh_token.sub
            user = session.execute(select(User).where(User.login==login)).fetchone()
            if user:
                access_token = create_token("access",{"sub":login},ACCESS_TOKEN_EXPIRE_MINUTES)
                return access_token
@app.get("/logout")
async def logout(session:Annotated[Session,Depends(get_db)],user:Annotated[UserSchema,Depends(get_current_user)]):
    session.execute(update(User).values(logged_in=False).where(User.login==user.login))
    session.commit()
    return {"status":"Logged out"}

@app.get("/tasks")
async def tasks(session:Annotated[Session,Depends(get_db)],currentUser:Annotated[UserSchema,Depends(get_current_user)]):
    return session.execute(select(Task).where(user=currentUser.login)).fetchall()
@app.post("/tasks")
async def task_add(task:TaskSchema,session:Annotated[Session,Depends(get_db)],currentUser:Annotated[UserSchema,Depends(get_current_user)]):
    try:
        session.execute(insert(Task).values(name=task.name,description=task.description,user=currentUser.login))
        return {"status":"Task added"}
    except:
        raise HTTPException(500,"Internal server error, task wasn't added")
@app.put("/tasks")
async def update_task(task:UpdateTask,session:Annotated[Session,Depends(get_db)],currentUser:Annotated[UserSchema,Depends(get_current_user)]):
    result = session.execute(select(Task).where(Task.id==task.id and Task.user==currentUser.login)).first()
    if not result:
        raise HTTPException(404,"Task wasn't found")
    try:
        session.execute(update(Task).values(name=task.name,description=task.description,status=task.status).where(Task.id == task.id))
        session.commit()
        return {"status":"Task was updated successfully"}
    except:
        raise HTTPException(500,"Internal server error, task wasn't updated")
@app.patch("/tasks")
async def update_task(task:PatchTask,session:Annotated[Session,Depends(get_db)],currentUser:Annotated[UserSchema,Depends(get_current_user)]):
    result = session.execute(select(Task).where(Task.id == task.id and Task.user == currentUser.login)).first()
    if not result:
        raise HTTPException(404, "Task wasn't found")
    if PatchTask.name:
        try:
            session.execute(
                update(Task).values(name=task.name).where(Task.id == task.id))
        except:
            raise HTTPException(500, "Internal server error, task wasn't updated")

    if PatchTask.description:
        try:
            session.execute(
                update(Task).values(description=task.description).where(Task.id == task.id))
        except:
            raise HTTPException(500, "Internal server error, task wasn't updated")
    if PatchTask.status:
        try:
            session.execute(
                update(Task).values(status=task.status).where(Task.id == task.id))
        except:
            raise HTTPException(500, "Internal server error, task wasn't updated")
    session.commit()
    return {"status":"Task was updated successfully"}
@app.delete("/tasks")
def delete_task(task:DeleteTask,session:Annotated[Session,Depends(get_db)],currentUser:Annotated[UserSchema,Depends(get_current_user)]):
    result = session.execute(select(Task).where(Task.id == task.id and Task.user == currentUser.login)).first()
    if not result:
        raise HTTPException(404, "Task wasn't found")
    try:
        session.execute(delete(Task).where(Task.id == task.id))
    except:
        raise HTTPException(500, "Internal server error, task wasn't updated")
    session.commit()
    return {"status":"Task was removed successfully"}