from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from settings import ALGORITHM, MAX_PASSWORD_LEN, SECRET_KEY

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/token/login')


def create_jwt(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get('sub')
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )


def is_authenticated(token: str = Depends(oauth2_scheme)) -> Optional[int]:
    return verify_jwt(token)


def password_format_is_valid(password: str) -> bool:
    return password and len(password) <= MAX_PASSWORD_LEN


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def password_hash_is_valid(raw_password, hashed_password) -> bool:
    return pwd_context.verify(raw_password, hashed_password)
