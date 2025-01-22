import jwt
from datetime import datetime, timedelta, timezone
from os import getenv
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

#убрать TEST, если уйдёт в production
SECRET_KEY = getenv("SECRET_KEY","TEST")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_TIME = timedelta(days=1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(typ:str, data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    to_encode.update({"typ": typ})
    encoded_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token

def decode_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except InvalidTokenError:
        return None

