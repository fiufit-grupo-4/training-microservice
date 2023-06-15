import jwt
from os import environ
from passlib.context import CryptContext
from pydantic import BaseSettings
from datetime import timedelta, datetime

from app.trainings.models import UserRoles

JWT_SECRET = environ.get("JWT_SECRET", "123456")
JWT_ALGORITHM = environ.get("JWT_ALGORITHM", "HS256")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
RESET_PASSWORD_EXPIRATION_MINUTES = environ.get("RESET_PASSWORD_EXPIRATION_MINUTES", 60)
EXPIRES = timedelta(minutes=int(RESET_PASSWORD_EXPIRATION_MINUTES))


class Settings(BaseSettings):
    @staticmethod
    def generate_token(id: str) -> str:
        utcnow = datetime.utcnow()
        expires = utcnow + EXPIRES
        token_data = {
            "id": id,
            "exp": expires,
            "iat": utcnow,
        }
        token = jwt.encode(token_data, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    def generate_token_with_role(id: str, role: UserRoles) -> str:
        utcnow = datetime.utcnow()
        expires = utcnow + EXPIRES
        token_data = {"id": id, "exp": expires, "iat": utcnow, "role": role}
        token = jwt.encode(token_data, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
