from pydantic import BaseModel



class Token(BaseModel):
    type: str
    token: str

class TokenData(BaseModel):
    login: str

class User(BaseModel):
    login: str
    password: str

class Task(BaseModel):
    name:str
    description:str
    status:bool

class UpdateTask(Task):
    id:int

class PatchTask(BaseModel):
    id:int
    name:str|None
    description:str|None
    status:bool|None

class DeleteTask(BaseModel):
    id:int
